"""
LLM 服务 - 统一 AI 接口封装 + AI 阅卷官
支持 Gemini / OpenAI 兼容接口 (VectorEngine, DeepSeek 等)

v2.5: 新增 grade_subjective_question — 考研英语一主观题批改
       翻译题 + 写作题专用 Prompt 模板
       JSON 解析重试机制 (最多 2 次)

Author: Femo
Date: 2026-02-18
"""

from typing import Optional, Dict, Any
import json
import re
import httpx
from app.core.config import settings


class LLMService:
    """大语言模型服务 (Gemini / OpenAI 兼容)"""

    def __init__(self):
        self.provider = settings.AI_PROVIDER
        
        # 初始化 OpenAI 客户端 (用于 VectorEngine/DeepSeek)
        if self.provider == "openai":
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL
            )
            self.model = settings.OPENAI_MODEL
            self.api_key = settings.OPENAI_API_KEY # Ensure attribute exists for checks
        
        # 初始化 Google 客户端
        elif self.provider == "gemini":
            self.api_key = settings.GEMINI_API_KEY
            self.base_url = settings.GEMINI_BASE_URL
            self.model = settings.GEMINI_MODEL

    # ==================================================================
    #  通用生成
    # ==================================================================

    async def generate(
        self,
        prompt: str,
        image_base64: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        history: list = None
    ) -> str:
        # Compatibility wrapper for sync-like access if needed, 
        # but preferably use generate_stream
        full_result = ""
        async for chunk in self.generate_stream(prompt, image_base64, system_prompt, temperature, max_tokens, history):
            full_result += chunk
        return full_result

    async def generate_stream(
        self,
        prompt: str,
        image_base64: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        history: list = None,
        # Added default None for image_base64 just in case, though it's already in sig
    ):
        """Streaming generator that supports conversation history"""
        history = history or []
        
        if self.provider == "openai":
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # Append history (ensure role is correct)
            # Append history (ensure role is correct)
            for msg in history:
                role = "assistant" if msg["role"] == "assistant" else "user"
                messages.append({"role": role, "content": msg["content"]})
            
            # 直接使用 self.model，绝对不允许任何 overrides!
            current_model = self.model 
            
            if image_base64:
                 if not image_base64.startswith("data:"):
                     img_url = f"data:image/jpeg;base64,{image_base64}"
                 else:
                     img_url = image_base64

                 user_content = [
                     {"type": "text", "text": prompt},
                     {"type": "image_url", "image_url": {"url": img_url}}
                 ]
                 messages.append({"role": "user", "content": user_content})
            else:
                messages.append({"role": "user", "content": prompt})

            stream = await self.client.chat.completions.create(
                model=current_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            async for chunk in stream:
                content = chunk.choices[0].delta.content or ""
                if content:
                    yield content

        elif self.provider == "gemini":
            # Construct Google-style chat history
            # Google Generative AI syntax: model.start_chat(history=[...])
            # But here we use raw HTTP for simplicity or sdk
            
            # Since we implement via HTTP in _generate_gemini, let's adapt it to stream.
            # However, standard HTTP streaming for Gemini requires specific endpoint/handling.
            # To keep it robust without rewriting the whole HTTP client for stream, 
            # I'll use the google-generativeai SDK if available, OR just fallback to simple logic?
            # Existing code uses httpx.AsyncClient(). Let's stick to that but use stream=True endpoint?
            # Gemini API "streamGenerateContent" endpoint: .../models/{model}:streamGenerateContent
            
            url = f"{self.base_url}/{self.model}:streamGenerateContent?alt=sse"
            
            contents = []
            if system_prompt:
                # Gemini system prompt is usually passed in generationConfig or as first 'user'/'model' turn?
                # Official API supports 'system_instruction' now, or we just prepend to first user message.
                # Let's verify existing logic: existing just prepended to prompt.
                # For history support, we need to map internal history to Gemini contents.
                pass
            
            # Map history
            # Gemini roles: 'user' -> 'user', 'assistant' -> 'model'
            for msg in history:
                role = "model" if msg["role"] == "assistant" else "user"
                contents.append({"role": role, "parts": [{"text": msg["content"]}]})
            
            # Current turn
            # If system_prompt is handled as prepend:
            final_prompt = prompt
            if system_prompt and not history:
                 final_prompt = f"{system_prompt}\n\n{prompt}"
            elif system_prompt and history:
                 # Check previous comments
                 if contents:
                     contents[0]["parts"][0]["text"] = f"{system_prompt}\n\n{contents[0]['parts'][0]['text']}"
                 else:
                     final_prompt = f"{system_prompt}\n\n{prompt}"
            
            user_parts = [{"text": final_prompt}]
            if image_base64:
                # Gemini inline data
                # Remove data prefix if present for Gemini 'inlineData' which expects raw base64
                raw_b64 = image_base64
                if "base64," in raw_b64:
                    raw_b64 = raw_b64.split("base64,")[1]
                
                user_parts.append({
                    "inlineData": {
                        "mimeType": "image/jpeg",
                        "data": raw_b64
                    }
                })

            contents.append({"role": "user", "parts": user_parts})

            payload = {
                "contents": contents,
                "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
            }
            headers = {"Content-Type": "application/json", "x-goog-api-key": self.api_key}

            async with httpx.AsyncClient() as client:
                async with client.stream("POST", url, json=payload, headers=headers, timeout=60.0) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if line.startswith("data:"):
                            try:
                                data = json.loads(line[5:])
                                chunk = data["candidates"][0]["content"]["parts"][0]["text"]
                                if chunk:
                                    yield chunk
                            except Exception:
                                pass

    async def generate_block(
        self,
        prompt: str,
        image_base64: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """Non-streaming generation for internal logic (more robust)"""
        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        
        content = [{"type": "text", "text": prompt}]
        if image_base64:
             if not image_base64.startswith("data:"):
                 img_url = f"data:image/jpeg;base64,{image_base64}"
             else:
                 img_url = image_base64
             content.append({"type": "image_url", "image_url": {"url": img_url}})
        
        msgs.append({"role": "user", "content": content})

        if self.provider == "openai":
            try:
                resp = await self.client.chat.completions.create(
                    model=self.model,
                    messages=msgs,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=False
                )
                return resp.choices[0].message.content or ""
            except Exception as e:
                with open("llm_debug.log", "a") as f:
                    f.write(f"generate_block Error: {e}\n")
                raise e
        else:
            # Fallback to stream if not openai (Gemini implementation in generate_stream)
            return await self.generate(prompt, image_base64, system_prompt, temperature, max_tokens)

    # ==================================================================
    #  AI 阅卷官 — 主观题批改 (翻译 + 写作)
    # ==================================================================

    async def grade_subjective_question(
        self,
        question_type: str,
        user_text: str,
        standard_answer: str = "",
        context_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        AI 批改主观题。自动选择翻译 / 写作 Prompt 模板。
        """
        context_info = context_info or {}

        # 选择 Prompt 模板
        if question_type == "translation":
            system_prompt, user_prompt = self._build_translation_prompt(
                user_text, standard_answer, context_info
            )
        else:
            system_prompt, user_prompt = self._build_writing_prompt(
                question_type, user_text, context_info
            )

        # 尝试调用 LLM (含 JSON 解析重试)
        for attempt in range(2):
            try:
                raw = await self.generate_block(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    image_base64=context_info.get("image_base64"),
                    temperature=0.3,
                    max_tokens=1000,
                )
                with open("llm_debug.log", "a") as f:
                    f.write(f"Attempt {attempt} RAW RESPONSE:\n{raw}\n" + "-"*20 + "\n")
                parsed = self._extract_json(raw)
                if parsed and "score" in parsed:
                    return parsed
            except Exception as e:
                with open("llm_debug.log", "a") as f:
                    import traceback
                    f.write(f"Attempt {attempt} failed: {e}\n")
                    f.write(traceback.format_exc())
                    f.write("\n")
                if attempt == 0:
                    continue  # 重试一次
                # 第二次仍失败 → fallback
                break

        # Fallback: API 不可用时返回 Mock
        return self._mock_grade(question_type, user_text)

    # ---- 翻译题 Prompt 模板 ----

    @staticmethod
    def _build_translation_prompt(
        user_text: str, standard_answer: str, ctx: Dict
    ) -> tuple:
        source_text = ctx.get("source_text", "(source text not provided)")

        system = (
            "Role: You are a strict grader for the "
            '"Postgraduate Entrance Exam English I" (考研英语一).\n'
            "Task: Grade the student's translation of a specific sentence.\n"
            "Max Score: 2.0 points.\n\n"
            f"[Source Sentence]: {source_text}\n"
            f"[Standard Answer]: {standard_answer}\n"
            f"[Student Answer]: {user_text}\n\n"
            "Grading Criteria:\n"
            "1. Accuracy (1.0 pt): Key vocabulary and sentence structure.\n"
            "2. Fluency (1.0 pt): Is the Chinese expression natural?\n"
            "3. Critical Errors: Deduct 0.5 for major mistranslation of key "
            "grammar points (e.g., inverted sentences, attributive clauses).\n\n"
            "Output JSON only:\n"
            "{\n"
            '    "score": <float, 0.0 to 2.0, step 0.5>,\n'
            '    "feedback": "<Brief comment in Chinese, max 50 words, '
            "using Mia's persona (猫娘语气)>\",\n"
            '    "key_points_missed": ["<list of missed vocab/grammar>"]\n'
            "}"
        )
        user = f"Please grade the student's translation and return JSON."
        return system, user

    # ---- 写作题 Prompt 模板 ----

    @staticmethod
    def _build_writing_prompt(
        question_type: str, user_text: str, ctx: Dict
    ) -> tuple:
        topic = ctx.get("topic", "(topic not provided)")
        if question_type == "writing_a":
            type_desc = "Writing A: Notice/Letter, Max 10 points"
        else:
            type_desc = "Writing B: Essay, Max 20 points"

        system = (
            'Role: You are a strict grader for "English I" Composition.\n'
            "Task: Grade the student's essay.\n"
            f"Type: {type_desc}\n\n"
            f"[Topic/Prompt]: {topic}\n"
            f"[Student Essay]: {user_text}\n\n"
            "Grading Criteria:\n"
            "1. Relevance: Did they stick to the topic?\n"
            "2. Vocabulary & Grammar: Variety and accuracy.\n"
            "3. Coherence: Logic flow.\n\n"
            "Output JSON only:\n"
            "{\n"
            '    "score": <float, e.g. 13.5>,\n'
            '    "feedback": "<Comment in Chinese, adopting the persona of a '
            "strict but encouraging cat-girl tutor Mia. Point out 1 major "
            'strength and 1 major weakness.>",\n'
            '    "suggestions": ["<Specific advice for improvement>"]\n'
            "}"
        )
        user = "Please grade the student's essay and return JSON."
        return system, user

    # ---- JSON 提取 (处理 LLM 返回的 markdown code block) ----

    @staticmethod
    def _extract_json(text: str) -> Optional[Dict]:
        """
        从 LLM 输出中提取 JSON，兼容以下格式:
          1. 纯 JSON
          2. ```json ... ```
          3. 混杂文本中的 {...}
        """
        # 尝试 1: 直接解析
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        # 尝试 2: 提取 ```json ... ```
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # 尝试 3: 提取第一个 { ... }
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    # ---- Mock 评分 (API 不可用时的兜底) ----

    @staticmethod
    def _mock_grade(question_type: str, user_text: str) -> Dict[str, Any]:
        """API 不可用时返回保守的 Mock 评分"""
        text_len = len(user_text.strip())

        if question_type == "translation":
            # 根据作答长度给一个保守分
            score = 1.0 if text_len > 10 else 0.5
            return {
                "score": score,
                "feedback": f"[Mock] 翻译字数 {text_len}，Mia 暂时无法联网批改喵~",
                "key_points_missed": ["(AI 离线, 无法分析)"],
            }
        else:
            max_score = 10.0 if question_type == "writing_a" else 20.0
            score = max_score * 0.6 if text_len > 50 else max_score * 0.4
            return {
                "score": score,
                "feedback": f"[Mock] 作文 {text_len} 字，Mia 暂时无法联网批改喵~",
                "suggestions": ["(AI 离线, 无法分析)"],
            }

    # ==================================================================
    #  Mia 对话生成 (保留旧接口)
    # ==================================================================

    async def generate_mia_response(
        self, user_action: str, hp_percentage: float,
        mood: str, context: Optional[Dict] = None,
    ) -> str:
        mood_prompts = {
            "energetic": "你是猫娘Mia,绯墨精神力充沛(HP>=80%),用崇拜开心的语气。",
            "focused": "你是猫娘Mia,绯墨状态良好(HP 30-80%),用专业鼓励的语气。",
            "warning": f"你是猫娘Mia,绯墨精神力很低(HP {hp_percentage:.1f}%),用心疼傲娇的语气。",
            "exhausted": "你是猫娘Mia,绯墨已力竭(HP=0),用关切语气要求他休息。",
        }
        system_prompt = mood_prompts.get(mood, mood_prompts["focused"])
        system_prompt += "\n回复简洁(100字内),可用emoji。"

        user_prompt = f"绯墨{user_action}"
        if context and "weak_words" in context:
            user_prompt += f"\n薄弱词汇: {', '.join(context['weak_words'][:3])}"

        return await self.generate(user_prompt, system_prompt, 0.8, 200)


# 单例
llm_service = LLMService()

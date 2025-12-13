"""从 EnglishExamWeb/data 构建带题目来源信息的词汇数据集。
以 2025考研英语7000词.csv 为主表，扫描历年真题寻找例句。
"""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any

class ExamVocabExtractor:
    """读取 CSV 词书和 EnglishExamWeb/data 下的试卷 JSON，构建全量词汇表。"""

    def __init__(self, project_root: Optional[Path] = None) -> None:
        self.project_root = Path(project_root or Path(__file__).resolve().parent.parent)
        self.data_dir = self.project_root / "EnglishExamWeb" / "data"
        self.csv_path = self.data_dir / "wordbooks" / "2025考研英语7000词.csv"
        self.output_path = self.project_root / "VocabWeb" / "data" / "exam_vocabulary.json"
        
        # word -> { definition, pos, sentences: [] }
        self.entries: Dict[str, Dict] = {}
        self.stats = defaultdict(int)

    def run(self) -> None:
        if not self.csv_path.exists():
            raise FileNotFoundError(f"未找到词书 CSV: {self.csv_path}")
        
        if not self.data_dir.exists():
            raise FileNotFoundError(f"未找到数据目录: {self.data_dir}")

        # 1. 加载 CSV 词书
        self._load_csv_wordbook()

        # 2. 扫描真题 JSON 寻找例句
        json_files = sorted(self.data_dir.glob("20*.json"))
        print(f"发现 {len(json_files)} 份试卷数据，开始扫描例句...")
        
        for file_path in json_files:
            with open(file_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            self._scan_exam_for_contexts(data, file_path.name)

        # 3. 导出
        self._export()

    def _load_csv_wordbook(self) -> None:
        print(f"正在加载词书: {self.csv_path.name} ...")
        count = 0
        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 2:
                    continue
                word = row[0].strip()
                definition_raw = row[1].strip()
                
                if not word:
                    continue

                # 简单的词性提取 (提取开头的 n. v. adj. 等)
                pos_match = re.match(r"([a-z]+\.)", definition_raw)
                pos = pos_match.group(1) if pos_match else ""

                self.entries[word] = {
                    "word": word,
                    "meanings": [definition_raw],
                    "pos": pos,
                    "sentences": []
                }
                count += 1
        print(f"已加载 {count} 个单词。")

    def _scan_exam_for_contexts(self, data: Dict, filename: str) -> None:
        meta = data.get("meta", {})
        year = meta.get("year")
        exam_type = meta.get("exam_type", "English")
        sections = data.get("sections", [])

        print(f"  · 扫描 {year} ({filename})...")
        
        for index, section in enumerate(sections, start=1):
            self._scan_section(section, year, exam_type, index)

    def _scan_section(self, section: Dict, year: int, exam_type: str, section_index: int) -> None:
        section_info = section.get("section_info") or {}
        section_name = section_info.get("name") or f"Section {section_index}"
        
        texts = self._extract_all_texts(section)
        
        for text_item in texts:
            text = text_item["text"]
            if not isinstance(text, str):
                continue
            question_number = text_item.get("q_num")
            
            # 分词
            tokens = set(re.findall(r"\b[a-zA-Z]{2,}\b", text))
            
            for token in tokens:
                word_lower = token.lower()
                if word_lower in self.entries:
                    self._add_context(word_lower, text, year, exam_type, section_name, question_number)
                
                # 简单的形态还原尝试
                if word_lower.endswith('s') and word_lower[:-1] in self.entries:
                     self._add_context(word_lower[:-1], text, year, exam_type, section_name, question_number)
                elif word_lower.endswith('ed') and word_lower[:-2] in self.entries:
                     self._add_context(word_lower[:-2], text, year, exam_type, section_name, question_number)
                elif word_lower.endswith('ing') and word_lower[:-3] in self.entries:
                     self._add_context(word_lower[:-3], text, year, exam_type, section_name, question_number)

    def _extract_all_texts(self, node: Any) -> List[Dict]:
        results = []
        if isinstance(node, dict):
            if "content" in node and isinstance(node["content"], str):
                results.append({"text": node["content"], "q_num": None})
            if "questions" in node:
                for q in node["questions"]:
                    q_num = q.get("number")
                    if "text" in q:
                        results.append({"text": q["text"], "q_num": q_num})
                    if "options" in q:
                        for opt in q["options"]:
                            if "content" in opt:
                                results.append({"text": opt["content"], "q_num": q_num})
            for key, value in node.items():
                if key not in ["content", "questions"]:
                    results.extend(self._extract_all_texts(value))
        elif isinstance(node, list):
            for item in node:
                results.extend(self._extract_all_texts(item))
        return results

    def _add_context(self, word: str, sentence: str, year: int, exam_type: str, section_name: str, q_num: Optional[int]) -> None:
        entry = self.entries[word]
        if len(entry["sentences"]) >= 3:
            return
        for s in entry["sentences"]:
            if s["sentence"] == sentence:
                return

        source_label = f"{year} {exam_type} · {section_name}"
        if q_num:
            source_label += f" (Q{q_num})"

        entry["sentences"].append({
            "sentence": sentence,
            "translation": "",
            "year": year,
            "exam_type": exam_type,
            "section_name": section_name,
            "question_number": q_num,
            "source_label": source_label
        })
        self.stats["contexts_found"] += 1

    def _export(self) -> None:
        output_data = list(self.entries.values())
        output_data.sort(key=lambda x: (len(x["sentences"]) == 0, x["word"]))
        
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
            
        print(f"\n导出完成: {self.output_path}")
        print(f"总单词数: {len(output_data)}")
        print(f"找到例句总数: {self.stats['contexts_found']}")
        covered = sum(1 for x in output_data if len(x["sentences"]) > 0)
        print(f"真题覆盖单词数: {covered} ({covered/len(output_data):.1%})")

if __name__ == "__main__":
    extractor = ExamVocabExtractor()
    extractor.run()

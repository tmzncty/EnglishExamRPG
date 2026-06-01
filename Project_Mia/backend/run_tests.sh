#!/bin/bash
# ==========================================================================
#  Project Mia — Test Runner
#  一键运行所有测试，输出清晰的 pass/fail 报告
#
#  用法:
#    ./run_tests.sh              # 运行全部测试
#    ./run_tests.sh -k "sm2"     # 按关键字过滤
#    ./run_tests.sh tests/test_sm2.py  # 指定文件
# ==========================================================================

set -e

echo "══════════════════════════════════════════════════"
echo "  🧪 Project Mia — Test Suite"
echo "══════════════════════════════════════════════════"

cd "$(dirname "$0")"

# Activate venv
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "❌ Virtualenv not found at venv/bin/activate"
    exit 1
fi

echo ""
echo "📦 Checking test dependencies..."
pip install pytest pytest-asyncio httpx --quiet 2>&1 | tail -1

echo ""
echo "📊 Test Plan:"
echo "   T1 🔴 Backend API   — exam, vocab, agent, user"
echo "   T2 🟠 Core Logic    — game_mechanics, sm2, helpers"
echo ""

# ── Run ──────────────────────────────────────────
START_TIME=$(date +%s)

pytest tests/ \
    -v \
    --tb=short \
    --color=yes \
    --durations=10 \
    -p no:warnings \
    "$@"

EXIT_CODE=$?
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# ── Report ────────────────────────────────────────
echo ""
echo "══════════════════════════════════════════════════"
if [ $EXIT_CODE -eq 0 ]; then
    echo "  ✅ ALL TESTS PASSED  (${DURATION}s)"
else
    echo "  ❌ SOME TESTS FAILED  (${DURATION}s)"
    echo "     Exit code: $EXIT_CODE"
fi
echo "══════════════════════════════════════════════════"

exit $EXIT_CODE

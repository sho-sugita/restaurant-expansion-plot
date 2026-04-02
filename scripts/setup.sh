#!/bin/bash
set -e

echo "=== 飲食店出店プロット セットアップ ==="

# 仮想環境
python3 -m venv .venv
source .venv/bin/activate

# 依存関係
pip install -r requirements.txt

# Playwright ブラウザ
playwright install chromium

echo ""
echo "=== セットアップ完了 ==="
echo ""
echo "次のステップ:"
echo "  1. データ取得:"
echo "     source .venv/bin/activate"
echo "     python -m pipeline.build_dataset"
echo ""
echo "  2. アプリ起動:"
echo "     streamlit run app.py"
echo ""
echo "  3. Streamlit Community Cloud へのデプロイ:"
echo "     https://share.streamlit.io/ でリポジトリを登録"
echo "     Main file: app.py"

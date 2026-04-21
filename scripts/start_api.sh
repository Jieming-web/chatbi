#!/bin/bash

# ChatBI API 快速启动脚本
# 用法: bash scripts/start_api.sh（从 chatbi-application/ 根目录运行）

set -e

# 切换到项目根目录
cd "$(dirname "$0")/.."

# 颜色输出
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        ChatBI API 启动脚本                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"

# 检查 Python
echo -e "${YELLOW}[1/5] 检查 Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo "❌ 未安装 Python 3"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✓ $PYTHON_VERSION${NC}"

# 检查虚拟环境
echo -e "${YELLOW}[2/5] 检查虚拟环境...${NC}"
if [ -d "venv" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✓ 虚拟环境已激活${NC}"
else
    echo -e "${YELLOW}⚠ 创建虚拟环境...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    echo -e "${GREEN}✓ 虚拟环境已创建${NC}"
fi

# 检查依赖
echo -e "${YELLOW}[3/5] 安装依赖...${NC}"
pip install -q -r requirements-api.txt
echo -e "${GREEN}✓ 依赖已安装${NC}"

# 检查环境变量
echo -e "${YELLOW}[4/5] 检查环境变量...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}  → 找不到 .env，复制 .env.example...${NC}"
        cp .env.example .env
        echo -e "${YELLOW}  ⚠ 请编辑 .env 并设置 DEEPSEEK_API_KEY${NC}"
    else
        echo -e "${YELLOW}  → 创建 .env 文件...${NC}"
        cat > .env << EOF
DEEPSEEK_API_KEY=
API_HOST=0.0.0.0
API_PORT=8000
EOF
        echo -e "${YELLOW}  ⚠ 请编辑 .env 并设置 DEEPSEEK_API_KEY${NC}"
    fi
fi

# 加载环境变量
set -a
source .env
set +a

if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo -e "${YELLOW}  ⚠ 警告：DEEPSEEK_API_KEY 未设置${NC}"
fi
echo -e "${GREEN}✓ 环境变量已加载${NC}"

# 启动 API
echo -e "${YELLOW}[5/5] 启动 API 服务...${NC}"
echo ""
echo -e "${GREEN}════════════════════════════════════════════${NC}"
echo -e "${GREEN}ChatBI API 运行中：http://localhost:8000${NC}"
echo -e "${GREEN}API 文档：http://localhost:8000/docs${NC}"
echo -e "${GREEN}按 CTRL+C 停止服务${NC}"
echo -e "${GREEN}════════════════════════════════════════════${NC}"
echo ""

uvicorn api:app --host ${API_HOST:-0.0.0.0} --port ${API_PORT:-8000} --reload

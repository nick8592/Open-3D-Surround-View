#!/usr/bin/env bash
# run_pipeline.sh
# Sequentially executes the full SVM pipeline:
#   1. Synthetic capture   (Blender – skipped if no scene file provided)
#      └─ capture_intrinsic, capture_extrinsic
#   2. Calibration         (intrinsic → extrinsic)
#      └─ calibrate_intrinsic, calibrate_extrinsic
#   3. BEV 2D              (stitch → render)
#      └─ stitching_bev, render_bev
#   4. Bowl 3D             (build → stitch → render)
#      └─ build_bowl, stitching_bowl, render_bowl
#   5. GPU asset export
#
# Use --skip-<stage> to skip a full stage, or --skip-<step> for a single script.
# Run with -h for full flag reference.

set -euo pipefail

# ── Resolve project root ────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Helpers ─────────────────────────────────────────────────────────────────
BOLD='\033[1m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; RED='\033[0;31m'; NC='\033[0m'

log_stage()  { echo -e "\n${BOLD}${GREEN}▶ $*${NC}"; }
log_info()   { echo -e "  ${YELLOW}→${NC} $*"; }
log_skip()   { echo -e "  ${YELLOW}⚠ SKIP:${NC} $*"; }
log_error()  { echo -e "  ${RED}✗ ERROR:${NC} $*" >&2; }

run_py() {
    log_info "python3 $*"
    python3 "$@"
}

run_blender() {
    local scene="$1"; shift
    log_info "blender -b $scene -P $*"
    blender -b "$scene" -P "$@"
}

# ── CLI options ──────────────────────────────────────────────────────────────
SCENE_FILE=""        # path to .blend file (required for capture stage)

# Stage-level skips
SKIP_CAPTURE=0
SKIP_CALIBRATION=0
SKIP_BEV=0
SKIP_BOWL=0
SKIP_GPU=0

# Step-level skips (capture)
SKIP_CAPTURE_INTRINSIC=0
SKIP_CAPTURE_EXTRINSIC=0

# Step-level skips (calibration)
SKIP_CALIBRATE_INTRINSIC=0
SKIP_CALIBRATE_EXTRINSIC=0

# Step-level skips (bev)
SKIP_BEV_STITCH=0
SKIP_BEV_RENDER=0

# Step-level skips (bowl)
SKIP_BOWL_BUILD=0
SKIP_BOWL_STITCH=0
SKIP_BOWL_RENDER=0

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Stage-level flags (skip entire stage):"
    echo "  -s, --scene <file>              Path to Blender .blend scene file (required for capture)"
    echo "  --skip-capture                  Skip entire synthetic capture stage"
    echo "  --skip-calibration              Skip entire calibration stage"
    echo "  --skip-bev                      Skip entire BEV 2D stage"
    echo "  --skip-bowl                     Skip entire Bowl 3D stage"
    echo "  --skip-gpu                      Skip GPU asset export stage"
    echo ""
    echo "Step-level flags (skip individual scripts):"
    echo "  --skip-capture-intrinsic        Skip capture_intrinsic.py"
    echo "  --skip-capture-extrinsic        Skip capture_extrinsic.py"
    echo "  --skip-calibrate-intrinsic      Skip calibrate_intrinsic.py"
    echo "  --skip-calibrate-extrinsic      Skip calibrate_extrinsic.py"
    echo "  --skip-bev-stitch               Skip stitching_bev.py"
    echo "  --skip-bev-render               Skip render_bev.py"
    echo "  --skip-bowl-build               Skip build_bowl.py"
    echo "  --skip-bowl-stitch              Skip stitching_bowl.py"
    echo "  --skip-bowl-render              Skip render_bowl.py"
    echo ""
    echo "  -h, --help                      Show this help message"
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -s|--scene)                  SCENE_FILE="$2";           shift 2 ;;
        --skip-capture)              SKIP_CAPTURE=1;             shift ;;
        --skip-calibration)          SKIP_CALIBRATION=1;         shift ;;
        --skip-bev)                  SKIP_BEV=1;                 shift ;;
        --skip-bowl)                 SKIP_BOWL=1;                shift ;;
        --skip-gpu)                  SKIP_GPU=1;                 shift ;;
        --skip-capture-intrinsic)    SKIP_CAPTURE_INTRINSIC=1;   shift ;;
        --skip-capture-extrinsic)    SKIP_CAPTURE_EXTRINSIC=1;   shift ;;
        --skip-calibrate-intrinsic)  SKIP_CALIBRATE_INTRINSIC=1; shift ;;
        --skip-calibrate-extrinsic)  SKIP_CALIBRATE_EXTRINSIC=1; shift ;;
        --skip-bev-stitch)           SKIP_BEV_STITCH=1;          shift ;;
        --skip-bev-render)           SKIP_BEV_RENDER=1;          shift ;;
        --skip-bowl-build)           SKIP_BOWL_BUILD=1;          shift ;;
        --skip-bowl-stitch)          SKIP_BOWL_STITCH=1;         shift ;;
        --skip-bowl-render)          SKIP_BOWL_RENDER=1;         shift ;;
        -h|--help)                   usage ;;
        *) log_error "Unknown option: $1"; usage ;;
    esac
done

echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}  SVM Pipeline Runner${NC}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# ── Stage 1: Synthetic Capture ───────────────────────────────────────────────
log_stage "Stage 1 / 5 — Synthetic Capture"
if [[ "$SKIP_CAPTURE" -eq 1 ]]; then
    log_skip "Capture stage skipped (--skip-capture)"
elif [[ -z "$SCENE_FILE" ]]; then
    log_skip "No --scene file provided; skipping capture stage"
elif [[ ! -f "$SCENE_FILE" ]]; then
    log_error "Scene file not found: $SCENE_FILE"
    exit 1
else
    if [[ "$SKIP_CAPTURE_INTRINSIC" -eq 1 ]]; then
        log_skip "capture_intrinsic.py (--skip-capture-intrinsic)"
    else
        run_blender "$SCENE_FILE" pipeline/synthetic_capture/capture_intrinsic.py
    fi
    if [[ "$SKIP_CAPTURE_EXTRINSIC" -eq 1 ]]; then
        log_skip "capture_extrinsic.py (--skip-capture-extrinsic)"
    else
        run_blender "$SCENE_FILE" pipeline/synthetic_capture/capture_extrinsic.py
    fi
fi

# ── Stage 2: Calibration ─────────────────────────────────────────────────────
log_stage "Stage 2 / 5 — Calibration"
if [[ "$SKIP_CALIBRATION" -eq 1 ]]; then
    log_skip "Calibration stage skipped (--skip-calibration)"
else
    if [[ "$SKIP_CALIBRATE_INTRINSIC" -eq 1 ]]; then
        log_skip "calibrate_intrinsic.py (--skip-calibrate-intrinsic)"
    else
        run_py pipeline/calibration/calibrate_intrinsic.py
    fi
    if [[ "$SKIP_CALIBRATE_EXTRINSIC" -eq 1 ]]; then
        log_skip "calibrate_extrinsic.py (--skip-calibrate-extrinsic)"
    else
        run_py pipeline/calibration/calibrate_extrinsic.py
    fi
fi

# ── Stage 3: BEV 2D ──────────────────────────────────────────────────────────
log_stage "Stage 3 / 5 — BEV 2D"
if [[ "$SKIP_BEV" -eq 1 ]]; then
    log_skip "BEV stage skipped (--skip-bev)"
else
    if [[ "$SKIP_BEV_STITCH" -eq 1 ]]; then
        log_skip "stitching_bev.py (--skip-bev-stitch)"
    else
        run_py pipeline/bev_2d/stitching_bev.py
    fi
    if [[ "$SKIP_BEV_RENDER" -eq 1 ]]; then
        log_skip "render_bev.py (--skip-bev-render)"
    else
        run_py pipeline/bev_2d/render_bev.py
    fi
fi

# ── Stage 4: Bowl 3D ─────────────────────────────────────────────────────────
log_stage "Stage 4 / 5 — Bowl 3D"
if [[ "$SKIP_BOWL" -eq 1 ]]; then
    log_skip "Bowl stage skipped (--skip-bowl)"
else
    if [[ "$SKIP_BOWL_BUILD" -eq 1 ]]; then
        log_skip "build_bowl.py (--skip-bowl-build)"
    else
        run_py pipeline/bowl_3d/build_bowl.py
    fi
    if [[ "$SKIP_BOWL_STITCH" -eq 1 ]]; then
        log_skip "stitching_bowl.py (--skip-bowl-stitch)"
    else
        run_py pipeline/bowl_3d/stitching_bowl.py
    fi
    if [[ "$SKIP_BOWL_RENDER" -eq 1 ]]; then
        log_skip "render_bowl.py (--skip-bowl-render)"
    else
        run_py pipeline/bowl_3d/render_bowl.py
    fi
fi

# ── Stage 5: GPU Asset Export ────────────────────────────────────────────────
log_stage "Stage 5 / 5 — GPU Asset Export"
if [[ "$SKIP_GPU" -eq 1 ]]; then
    log_skip "GPU export stage skipped (--skip-gpu)"
else
    run_py pipeline/gpu_render/export_gpu_assets.py
fi

echo -e "\n${BOLD}${GREEN}✔ Pipeline complete.${NC}\n"

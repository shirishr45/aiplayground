"""
Shear Tab Connection Detail
W8x31 beam framing into W10x49 column — elevation view
Units: inches
"""
import ezdxf
from ezdxf import units

# ── Section properties ─────────────────────────────────────────────────────────
# W8x31
B_d   = 8.00    # depth
B_bf  = 7.995   # flange width
B_tf  = 0.435   # flange thickness
B_tw  = 0.285   # web thickness
B_len = 30.0    # length of beam to show

# W10x49 column
C_d   = 9.98    # depth
C_bf  = 10.0    # flange width
C_tf  = 0.560   # flange thickness
C_tw  = 0.340   # web thickness
C_ht  = 24.0    # height of column to show

# Shear tab  PL3/8 x 6 x 0'-8"
T_t   = 0.375   # thickness
T_h   = 6.0     # height
T_w   = 4.0     # width (projection from column face)

# Bolts  3/4" A325 @ 3" spacing
BOLT_D   = 0.75
HOLE_D   = 0.8125   # 13/16" standard hole
N_BOLTS  = 2
BOLT_SP  = 3.0
BOLT_EV  = 1.5      # edge distance vertical
BOLT_EH  = 1.5      # edge distance from beam end

# ── Document setup ─────────────────────────────────────────────────────────────
doc = ezdxf.new("R2010")
doc.units = units.IN

# Layers
def add_layer(name, color, ltype="Continuous"):
    doc.layers.add(name, color=color, linetype=ltype)

add_layer("STEEL",   color=2)   # yellow  — main steel shapes
add_layer("PLATE",   color=3)   # green   — connection plate
add_layer("BOLT",    color=5)   # blue    — bolts / holes
add_layer("WELD",    color=1)   # red     — weld symbols
add_layer("TEXT",    color=7)   # white   — labels
add_layer("DIMS",    color=4)   # cyan    — dimensions
add_layer("CENTER",  color=6)   # magenta — centerlines

msp = doc.modelspace()

def pline(pts, layer, close=False):
    msp.add_lwpolyline(pts, dxfattribs={"layer": layer}, close=close)

def circle(center, radius, layer):
    msp.add_circle(center, radius, dxfattribs={"layer": layer})

def line(p1, p2, layer):
    msp.add_line(p1, p2, dxfattribs={"layer": layer})

def text(txt, insert, height, layer, halign=0):
    t = msp.add_text(txt, dxfattribs={"layer": layer, "height": height})
    t.set_placement(insert, align=ezdxf.enums.TextEntityAlignment.LEFT)

# ── Coordinate origin: beam centerline at column face ─────────────────────────
# Column face is at x=0; beam runs in +x direction; beam CL is y=0

# ── Column (drawn as I-shape in elevation) ─────────────────────────────────────
cx = -C_d / 2      # column centerline x (column spans from -C_d to 0)

col_pts = [
    # Start bottom-left of left flange, trace I-shape outline clockwise
    (-C_d,          -C_ht / 2),
    (-C_d + C_bf,   -C_ht / 2),    # this is wrong — let me draw correctly
]
# Column in elevation: two flanges (left & right) + web connecting them
# Left flange
pline([
    (-C_d,           -C_ht / 2),
    (-C_d + C_tf,    -C_ht / 2),
    (-C_d + C_tf,     C_ht / 2),
    (-C_d,            C_ht / 2),
], layer="STEEL", close=True)

# Right flange (column face side)
pline([
    (-C_tf,  -C_ht / 2),
    (0,      -C_ht / 2),
    (0,       C_ht / 2),
    (-C_tf,   C_ht / 2),
], layer="STEEL", close=True)

# Web connecting flanges
pline([
    (-C_d + C_tf,  -C_tw / 2),
    (-C_tf,        -C_tw / 2),
    (-C_tf,         C_tw / 2),
    (-C_d + C_tf,   C_tw / 2),
], layer="STEEL", close=True)

# Column centerline
line((-C_d / 2, -C_ht / 2 - 1), (-C_d / 2, C_ht / 2 + 1), layer="CENTER")

# ── Beam W8x31 ────────────────────────────────────────────────────────────────
# Top flange
pline([
    (0,      B_d / 2),
    (B_len,  B_d / 2),
    (B_len,  B_d / 2 - B_tf),
    (0,      B_d / 2 - B_tf),
], layer="STEEL", close=True)

# Bottom flange
pline([
    (0,      -B_d / 2 + B_tf),
    (B_len,  -B_d / 2 + B_tf),
    (B_len,  -B_d / 2),
    (0,      -B_d / 2),
], layer="STEEL", close=True)

# Web
pline([
    (0,      B_d / 2 - B_tf),
    (B_len,  B_d / 2 - B_tf),
    (B_len, -B_d / 2 + B_tf),
    (0,     -B_d / 2 + B_tf),
], layer="STEEL", close=True)

# Beam centerline
line((-1, 0), (B_len + 1, 0), layer="CENTER")

# ── Shear Tab ─────────────────────────────────────────────────────────────────
tab_x0 = 0.0
tab_x1 = T_w
tab_y0 = -T_h / 2
tab_y1 =  T_h / 2

pline([
    (tab_x0, tab_y0),
    (tab_x1, tab_y0),
    (tab_x1, tab_y1),
    (tab_x0, tab_y1),
], layer="PLATE", close=True)

# ── Bolt holes ────────────────────────────────────────────────────────────────
bolt_x = BOLT_EH   # horizontal distance from column face
for i in range(N_BOLTS):
    by = -( (N_BOLTS - 1) * BOLT_SP / 2 ) + i * BOLT_SP
    circle((bolt_x, by), HOLE_D / 2,  layer="BOLT")
    circle((bolt_x, by), BOLT_D / 2,  layer="BOLT")   # bolt body (inner)

# ── Weld symbols (simplified as thick line at column face) ────────────────────
# Fillet weld on both sides of shear tab
line((0, tab_y0), (0, tab_y1), layer="WELD")

# ── Text labels ───────────────────────────────────────────────────────────────
text("W8x31",                   (B_len * 0.4,  B_d / 2 + 1.2), height=0.5, layer="TEXT")
text("W10x49",                  (-C_d / 2 - 1, C_ht / 2 + 1.5), height=0.5, layer="TEXT")
text("PL 3/8\"x6\"x0'-8\"",    (T_w + 0.5,  T_h / 2 + 0.5), height=0.4, layer="TEXT")
text(f"({N_BOLTS}) 3/4\" A325N", (bolt_x - 0.5, tab_y0 - 1.5), height=0.4, layer="TEXT")
text("1/4\" FILLET WELD",       (-C_d - 2,  0.5), height=0.4, layer="TEXT")

# ── Basic dimensions ──────────────────────────────────────────────────────────
# Beam depth
msp.add_linear_dim(
    base=(B_len + 2, 0),
    p1=(B_len + 1.5,  B_d / 2),
    p2=(B_len + 1.5, -B_d / 2),
    dimstyle="EZDXF",
    override={"dimtxt": 0.4},
).render()

# Tab height
msp.add_linear_dim(
    base=(tab_x1 + 1, 0),
    p1=(tab_x1 + 0.5,  T_h / 2),
    p2=(tab_x1 + 0.5, -T_h / 2),
    dimstyle="EZDXF",
    override={"dimtxt": 0.4},
).render()

# ── Save ──────────────────────────────────────────────────────────────────────
output = "shear_tab_detail.dxf"
doc.saveas(output)
print(f"Saved: {output}")
print("Open in AutoCAD, LibreCAD, or DraftSight.")

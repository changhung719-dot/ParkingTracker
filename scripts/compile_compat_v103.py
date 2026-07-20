from pathlib import Path

view = Path('ParkingLocationPayload/app/src/main/java/com/interfaceworld/parkinglocation/ParkingView.java')
s = view.read_text(encoding='utf-8')

# The restored payload has the compact 3-argument vehicle-card helper.
if 'private void drawVehicleCards(Canvas c, float x, float y)' in s:
    s = s.replace('drawVehicleCards(c, 22, 102, 86);', 'drawVehicleCards(c, 22, 102);')

# Some source revisions reference a compact recent-card icon helper but do not
# contain its implementation. Add the helper only when required.
if 'smallIconButton(c,' in s and 'private void smallIconButton(' not in s:
    anchor = '    private void smallButton('
    pos = s.index(anchor)
    helper = '''    private void smallIconButton(Canvas c, float x, float y, String label, boolean danger, Runnable action) {
        int accent = danger ? RED : BLUE;
        card(c, x, y, x + 34, y + 34, BORDER, Color.WHITE, 8, 1f);
        textCenterMiddle(c, label, x + 17, y + 17, 13f, accent, true);
        addHit(x, y, x + 34, y + 34, action);
    }

'''
    s = s[:pos] + helper + s[pos:]

view.write_text(s, encoding='utf-8')

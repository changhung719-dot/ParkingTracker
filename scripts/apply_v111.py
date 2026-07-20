from pathlib import Path
import re

root = Path('ParkingLocationPayload')

# Increment Android package version for an in-place update.
gradle = root / 'app/build.gradle'
s = gradle.read_text(encoding='utf-8')
s = re.sub(r'versionCode\s+\d+', 'versionCode 11', s)
s = re.sub(r"versionName\s+'[^']+'", "versionName '1.0.11'", s)
s = re.sub(r'^\s*signingConfig signingConfigs\.debug\s*\n', '', s, flags=re.M)
gradle.write_text(s, encoding='utf-8')

view = root / 'app/src/main/java/com/interfaceworld/parkinglocation/ParkingView.java'
s = view.read_text(encoding='utf-8')

# Company parking now supports B1 through B5. Home parking remains unchanged.
s = s.replace('int max = idx == 0 ? 5 : 2;', 'int max = idx == 0 ? 5 : 4;')
s = s.replace(
    'new String[]{"지하1층", "지하2층", "지하3층"}',
    'new String[]{"지하1층", "지하2층", "지하3층", "지하4층", "지하5층"}'
)
s = s.replace(
    'new String[]{"지하 1층", "지하 2층", "지하 3층"}',
    'new String[]{"지하 1층", "지하 2층", "지하 3층", "지하 4층", "지하 5층"}'
)
s = s.replace(
    '{"지하1층", "지하2층", "지하3층"}',
    '{"지하1층", "지하2층", "지하3층", "지하4층", "지하5층"}'
)
s = s.replace(
    '{"지하 1층", "지하 2층", "지하 3층"}',
    '{"지하 1층", "지하 2층", "지하 3층", "지하 4층", "지하 5층"}'
)
s = s.replace('지하1층부터 지하3층', '지하1층부터 지하5층')
s = s.replace('지하 1층부터 지하 3층', '지하 1층부터 지하 5층')
s = s.replace('지하 1층~지하 3층', '지하 1층~지하 5층')

# Rebuild the parking screen with the same coordinates and functions as v1.0.10.
# The former company-only information box is replaced by the second row of B4/B5 buttons.
start = s.index('    private void drawHome(Canvas c) {')
end = s.index('    private void drawVehicleCards', start)
new_home = '''    private void drawHome(Canvas c) {
        int location = prefs.getInt("selected_location", 0);

        text(c, "주차위치", 22, 31, 29, TEXT, true);
        chip(c, 22, 44, 148, 74,
                prefs.getBool("auto_detect", true) ? "● 자동 감지 ON" : "● 자동 감지 OFF",
                BLUE, LIGHT_BLUE);
        bell(c, 352, 29, true);

        text(c, "내 차량", 22, 99, 15.5f, TEXT, true);
        drawVehicleCards(c, 22, 110, 108);

        text(c, "위치 유형", 22, 243, 15.5f, TEXT, true);
        segment(c, 22, 254, 368, 302, new String[]{"⌂  집", "▦  회사"}, location, idx -> {
            prefs.putInt("selected_location", idx);
            int max = idx == 0 ? 5 : 4;
            if (prefs.getInt("selected_floor", 0) > max) prefs.putInt("selected_floor", max);
        });

        text(c, location == 0 ? "층 선택 (집 주차장)" : "층 선택 (회사 주차장)",
                22, 329, 15.5f, TEXT, true);
        drawFloors(c, location, 22, 342);

        button(c, 22, 440, 368, 495, "현재 주차 위치 저장", true, this::saveParking);

        text(c, "최근 저장 위치", 22, 526, 15.5f, TEXT, true);
        drawRecentCard(c, 0, 22, 541);
        drawRecentCard(c, 1, 22, 634);

        drawBottomNav(c, 1);
    }

'''
s = s[:start] + new_home + s[end:]

# Replace the floor-grid method so both locations display two compact rows.
start = s.index('    private void drawFloors')
end = s.index('    private ', start + len('    private void drawFloors'))
new_floors = '''    private void drawFloors(Canvas c, int location, float x, float y) {
        String[] labels = location == 0
                ? new String[]{"1층", "지하1층", "지하2층", "지하3층", "지하4층", "지하5층"}
                : new String[]{"지하1층", "지하2층", "지하3층", "지하4층", "지하5층"};
        int selected = prefs.getInt("selected_floor", location == 0 ? 3 : 0);
        float gap = 10f;
        float w = (346f - 2f * gap) / 3f;
        for (int i = 0; i < labels.length; i++) {
            int row = i / 3;
            int col = i % 3;
            float l = x + col * (w + gap);
            float t = y + row * 46f;
            boolean on = selected == i;
            smallButton(c, l, t, l + w, t + 40f, labels[i], on);
            int idx = i;
            addHit(l, t, l + w, t + 40f, () -> prefs.putInt("selected_floor", idx));
        }
    }

'''
s = s[:start] + new_floors + s[end:]

# Defensive replacements for save/edit floor arrays after the method rewrite.
s = s.replace(
    'String[] labels = {"지하 1층", "지하 2층", "지하 3층"};',
    'String[] labels = {"지하 1층", "지하 2층", "지하 3층", "지하 4층", "지하 5층"};'
)
s = s.replace(
    'String[] labels = {"지하1층", "지하2층", "지하3층"};',
    'String[] labels = {"지하1층", "지하2층", "지하3층", "지하4층", "지하5층"};'
)
s = s.replace(
    'String[] f = {"지하 1층", "지하 2층", "지하 3층"};',
    'String[] f = {"지하 1층", "지하 2층", "지하 3층", "지하 4층", "지하 5층"};'
)
s = s.replace(
    'String[] f = {"지하1층", "지하2층", "지하3층"};',
    'String[] f = {"지하1층", "지하2층", "지하3층", "지하4층", "지하5층"};'
)

# Increase typography on every page by 8 percent. This affects parking,
# settings, engine-oil/vehicle management, buttons, cards, and bottom navigation.
# Layout coordinates and touch targets are deliberately left unchanged.
if 'p.setTextSize(size * 1.08f);' not in s:
    count = s.count('p.setTextSize(size);')
    if count < 2:
        raise RuntimeError(f'Expected text-size helpers, found {count}')
    s = s.replace('p.setTextSize(size);', 'p.setTextSize(size * 1.08f);')

view.write_text(s, encoding='utf-8')

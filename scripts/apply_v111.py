from pathlib import Path
import re

root = Path('ParkingLocationPayload')

gradle = root / 'app/build.gradle'
s = gradle.read_text(encoding='utf-8')
s = re.sub(r'versionCode\s+\d+', 'versionCode 11', s)
s = re.sub(r"versionName\s+'[^']+'", "versionName '1.0.11'", s)
s = re.sub(r'^\s*signingConfig signingConfigs\.debug\s*\n', '', s, flags=re.M)
gradle.write_text(s, encoding='utf-8')

view = root / 'app/src/main/java/com/interfaceworld/parkinglocation/ParkingView.java'
s = view.read_text(encoding='utf-8')

# 회사 주차장은 B1층부터 B5층까지 선택할 수 있습니다.
s = s.replace('int max = idx == 0 ? 5 : 2;', 'int max = idx == 0 ? 5 : 4;')

# 기존 화면 배치와 기능은 유지하면서 회사 층수만 5개로 확장합니다.
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

start = s.index('    private void drawFloors')
end = s.index('    private void saveParking()', start)
new_floors = '''    private void drawFloors(Canvas c, int location, float x, float y) {
        String[] labels = location == 0
                ? new String[]{"1층", "지하1층", "지하2층", "지하3층", "지하4층", "지하5층"}
                : new String[]{"B1층", "B2층", "B3층", "B4층", "B5층"};
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

# 저장 로직의 회사 층수 배열도 B1~B5로 맞춥니다.
s = s.replace(
    'String[] labels = {"지하1층", "지하2층", "지하3층"};',
    'String[] labels = {"B1층", "B2층", "B3층", "B4층", "B5층"};')
s = s.replace(
    'String[] labels = {"지하 1층", "지하 2층", "지하 3층"};',
    'String[] labels = {"B1층", "B2층", "B3층", "B4층", "B5층"};')

# 과거 버전에서 저장한 지하1층~지하5층 값도 수정 화면에서 정상적으로 불러옵니다.
start = s.index('    private void editRecent(int vehicle) {')
end = s.index('    private void deleteRecent', start)
new_edit = '''    private void editRecent(int vehicle) {
        String loc = prefs.getString("park_" + vehicle + "_location", "집");
        String floor = prefs.getString("park_" + vehicle + "_floor", "지하1층");
        prefs.putInt("selected_vehicle", vehicle);
        int location = "회사".equals(loc) ? 1 : 0;
        prefs.putInt("selected_location", location);
        int idx = 0;
        String normalized = floor.replace(" ", "").toUpperCase();
        if (location == 0) {
            String[] values = {"1층", "지하1층", "지하2층", "지하3층", "지하4층", "지하5층"};
            for (int i = 0; i < values.length; i++) {
                if (values[i].equals(normalized)) idx = i;
            }
        } else {
            String[] values = {"B1층", "B2층", "B3층", "B4층", "B5층"};
            String[] legacy = {"지하1층", "지하2층", "지하3층", "지하4층", "지하5층"};
            for (int i = 0; i < values.length; i++) {
                if (values[i].equals(normalized) || legacy[i].equals(normalized)) idx = i;
            }
        }
        prefs.putInt("selected_floor", idx);
        screen = Screen.PARKING;
        host.showMessage("저장된 위치를 불러왔습니다. 수정 후 다시 저장하세요.");
    }

'''
s = s[:start] + new_edit + s[end:]

# 50대 사용자가 읽기 쉽도록 모든 페이지에서 작은 글자를 우선 확대합니다.
# 배치 좌표와 터치 영역은 변경하지 않습니다.
if 'private float readableTextSize(' not in s:
    anchor = '    private void text(Canvas c, String'
    pos = s.index(anchor)
    helper = '''    private float readableTextSize(float size) {
        if (size <= 10.5f) return size * 1.18f;
        if (size <= 13.5f) return size * 1.13f;
        if (size <= 18f) return size * 1.09f;
        return size * 1.04f;
    }

'''
    s = s[:pos] + helper + s[pos:]

s = s.replace('p.setTextSize(size);', 'p.setTextSize(readableTextSize(size));')
s = s.replace('p.setTextSize(size * 1.08f);', 'p.setTextSize(readableTextSize(size));')
s = s.replace('Typeface.create("sans-serif-medium", Typeface.NORMAL)',
              'Typeface.create("sans-serif", Typeface.BOLD)')
s = s.replace('Typeface.create("sans-serif", Typeface.NORMAL)',
              'Typeface.create("sans-serif", Typeface.BOLD)')
s = s.replace('Typeface.create("sans", Typeface.NORMAL)',
              'Typeface.create("sans-serif", Typeface.BOLD)')

view.write_text(s, encoding='utf-8')

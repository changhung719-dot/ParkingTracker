from pathlib import Path
import re

root = Path('ParkingLocationPayload')

# Android update version.
gradle = root / 'app/build.gradle'
s = gradle.read_text(encoding='utf-8')
s = re.sub(r'versionCode\s+\d+', 'versionCode 12', s)
s = re.sub(r"versionName\s+'[^']+'", "versionName '1.0.12'", s)
s = re.sub(r'^\s*signingConfig signingConfigs\.debug\s*\n', '', s, flags=re.M)
gradle.write_text(s, encoding='utf-8')

view = root / 'app/src/main/java/com/interfaceworld/parkinglocation/ParkingView.java'
s = view.read_text(encoding='utf-8')

# Parking page order follows the approved UI:
# recent locations -> vehicles -> location type -> floor -> save.
start = s.index('    private void drawHome(Canvas c) {')
end = s.index('    private void drawVehicleCards', start)
new_home = '''    private void drawHome(Canvas c) {
        int location = prefs.getInt("selected_location", 0);

        text(c, "주차위치", 22, 31, 29, TEXT, true);
        chip(c, 22, 44, 148, 74,
                prefs.getBool("auto_detect", true) ? "● 자동 감지 ON" : "● 자동 감지 OFF",
                BLUE, LIGHT_BLUE);
        bell(c, 352, 29, true);

        text(c, "최근 저장 위치", 22, 105, 15.5f, TEXT, true);
        drawRecentCard(c, 0, 22, 119);
        drawRecentCard(c, 1, 22, 204);

        text(c, "내 차량", 22, 310, 15.5f, TEXT, true);
        drawVehicleCards(c, 22, 320, 104);

        text(c, "위치 유형", 22, 451, 15.5f, TEXT, true);
        segment(c, 22, 462, 368, 510, new String[]{"⌂  집", "▦  회사"}, location, idx -> {
            prefs.putInt("selected_location", idx);
            int max = idx == 0 ? 5 : 4;
            if (prefs.getInt("selected_floor", 0) > max) prefs.putInt("selected_floor", max);
        });

        text(c, location == 0 ? "층 선택 (집 주차장)" : "층 선택 (회사 주차장)",
                22, 537, 15.5f, TEXT, true);
        drawFloors(c, location, 22, 550);

        button(c, 22, 652, 368, 716, "현재 주차 위치 저장", true, this::saveParking);
        drawBottomNav(c, 1);
    }

'''
s = s[:start] + new_home + s[end:]

# Home: 1F and B1-B5. Company: B1-B5.
start = s.index('    private void drawFloors(Canvas c, int location, float x, float y) {')
end = s.index('    private void saveParking()', start)
new_floors = '''    private void drawFloors(Canvas c, int location, float x, float y) {
        String[] labels = location == 0
                ? new String[]{"1층", "B1층", "B2층", "B3층", "B4층", "B5층"}
                : new String[]{"B1층", "B2층", "B3층", "B4층", "B5층"};
        int selected = prefs.getInt("selected_floor", location == 0 ? 0 : 0);
        if (selected >= labels.length) {
            selected = labels.length - 1;
            prefs.putInt("selected_floor", selected);
        }
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

start = s.index('    private void saveParking() {')
end = s.index('    private void drawRecentCard', start)
new_save = '''    private void saveParking() {
        int vehicle = prefs.getInt("selected_vehicle", 0);
        int location = prefs.getInt("selected_location", 0);
        int floorIndex = prefs.getInt("selected_floor", 0);
        String floor;
        if (location == 0) {
            String[] labels = {"1층", "B1층", "B2층", "B3층", "B4층", "B5층"};
            floor = labels[Math.max(0, Math.min(floorIndex, labels.length - 1))];
        } else {
            String[] labels = {"B1층", "B2층", "B3층", "B4층", "B5층"};
            floor = labels[Math.max(0, Math.min(floorIndex, labels.length - 1))];
        }
        prefs.saveParking(vehicle, location == 0 ? "집" : "회사", floor);
        host.cancelParkingReminder();
        host.showMessage(prefs.vehicleName(vehicle) + " · "
                + (location == 0 ? "집" : "회사") + " · " + floor + " 저장 완료");
    }

'''
s = s[:start] + new_save + s[end:]

# Compact but readable recent-location cards used at the top of the parking page.
start = s.index('    private void drawRecentCard')
end = s.index('    private void editRecent', start)
new_recent = '''    private void drawRecentCard(Canvas c, int vehicle, float x, float y) {
        String location = prefs.getString("park_" + vehicle + "_location", "");
        String floor = prefs.getString("park_" + vehicle + "_floor", "");
        String time = prefs.getString("park_" + vehicle + "_time", "-");

        card(c, x, y, x + 346, y + 76, BORDER, Color.WHITE, 12, 1f);
        drawVehicleIllustration(c, vehicle, x + 8, y + 8, x + 116, y + 68);

        text(c, prefs.vehicleName(vehicle), x + 120, y + 25, 16f, TEXT, true);
        if (location.isEmpty()) {
            text(c, "저장된 위치 없음", x + 120, y + 48, 12.5f, MUTED, true);
            text(c, "-", x + 120, y + 68, 10.5f, MUTED, true);
        } else {
            text(c, (location.equals("집") ? "⌂ " : "▦ ") + location + " / " + floor,
                    x + 120, y + 48, 12.5f, BLUE, true);
            text(c, time, x + 120, y + 68, 10.5f, MUTED, true);
        }

        drawActionButton(c, x + 266, y + 16, x + 309, y + 61,
                "수정", BLUE, () -> editRecent(vehicle));
        drawActionButton(c, x + 314, y + 16, x + 344, y + 61,
                "삭제", RED, () -> deleteRecent(vehicle));
    }

    private void drawActionButton(Canvas c, float l, float t, float r, float b,
                                  String label, int color, Runnable action) {
        card(c, l, t, r, b, BORDER, Color.WHITE, 8, 1f);
        textCenterMiddle(c, label, (l + r) / 2f, (t + b) / 2f,
                11f, color, true);
        addHit(l, t, r, b, action);
    }

'''
s = s[:start] + new_recent + s[end:]

# Previous Korean basement labels continue to load correctly after the B-label change.
start = s.index('    private void editRecent(int vehicle) {')
end = s.index('    private void deleteRecent', start)
new_edit = '''    private void editRecent(int vehicle) {
        String loc = prefs.getString("park_" + vehicle + "_location", "집");
        String floor = prefs.getString("park_" + vehicle + "_floor", "B1층");
        prefs.putInt("selected_vehicle", vehicle);
        int location = "회사".equals(loc) ? 1 : 0;
        prefs.putInt("selected_location", location);
        int idx = 0;
        String normalized = floor.replace(" ", "").toUpperCase();
        if (location == 0) {
            String[] values = {"1층", "B1층", "B2층", "B3층", "B4층", "B5층"};
            String[] legacy = {"1층", "지하1층", "지하2층", "지하3층", "지하4층", "지하5층"};
            for (int i = 0; i < values.length; i++) {
                if (values[i].equals(normalized) || legacy[i].equals(normalized)) idx = i;
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

# Vehicle / engine-oil page follows the approved layout while preserving input,
# save, alert, history, and per-vehicle functions.
start = s.index('    private void drawVehicle(Canvas c) {')
end = s.index('    private void drawNumberField', start)
new_vehicle = '''    private void drawVehicle(Canvas c) {
        text(c, "‹", 22, 34, 35, TEXT, true);
        text(c, "차량 관리 / 엔진오일", 55, 33, 23f, TEXT, true);
        addHit(10, 8, 48, 54, () -> screen = Screen.HOME);

        segment(c, 22, 72, 368, 116, new String[]{"셀토스", "G90"}, oilVehicle,
                idx -> oilVehicle = idx);

        int current = prefs.getInt("oil_" + oilVehicle + "_current", 0);
        int last = prefs.getInt("oil_" + oilVehicle + "_last", 0);
        int next = prefs.getInt("oil_" + oilVehicle + "_next", 0);

        drawNumberField(c, "현재 주행거리(km)", "oil_" + oilVehicle + "_current",
                current, 22, 136, "◴");
        drawNumberField(c, "마지막 엔진오일 교환 km", "oil_" + oilVehicle + "_last",
                last, 22, 236, "♨");
        drawNumberField(c, "다음 엔진오일 교환 예정 km", "oil_" + oilVehicle + "_next",
                next, 22, 336, "▣");

        boolean ready = current > 0 && next > 0;
        int remain = ready ? next - current : 0;
        int interval = last > 0 && next > last ? next - last : 10000;
        card(c, 22, 438, 368, 531, Color.rgb(196, 218, 249), LIGHT_BLUE, 12, 1f);
        gauge(c, 66, 484, remain, Math.max(1000, interval));
        textCenter(c, ready && remain < 0 ? "교환 예정 거리 초과" : "다음 교환까지",
                235, 473, 13f, TEXT, true);
        String remainText = ready
                ? NumberFormat.getNumberInstance(Locale.KOREA).format(Math.abs(remain))
                    + "km " + (remain >= 0 ? "남음" : "초과")
                : "km 남음";
        textCenter(c, remainText, 235, 504, 27f,
                ready && remain < 0 ? RED : BLUE, true);

        button(c, 22, 551, 368, 601, "저장", true, () -> {
            prefs.putString("oil_" + oilVehicle + "_history", "엔진오일 정보 저장");
            host.showMessage(prefs.vehicleName(oilVehicle) + " 엔진오일 정보를 저장했습니다.");
        });
        button(c, 22, 612, 368, 662, "♧  알림 설정", false,
                () -> host.showMessage("다음 교환 예정 거리 도달 시 알림을 안내합니다."));

        text(c, "정비 이력", 22, 695, 13f, TEXT, true);
        text(c, "전체 보기 ›", 302, 695, 10.8f, BLUE, true);
        card(c, 22, 705, 368, 735, BORDER, Color.WHITE, 8, 1f);
        text(c, "2024.03.15", 35, 725, 10f, MUTED, true);
        String lastText = last > 0
                ? NumberFormat.getNumberInstance(Locale.KOREA).format(last) + "km" : "km";
        textCenter(c, lastText, 198, 725, 10f, MUTED, true);
        text(c, "엔진오일 교환  ›", 268, 725, 10f, TEXT, true);
        drawBottomNav(c, 2);
    }

'''
s = s[:start] + new_vehicle + s[end:]

start = s.index('    private void drawNumberField')
end = s.index('    private void drawBottomNav', start)
new_number = '''    private void drawNumberField(Canvas c, String label, String key, int value,
                                 float x, float y, String icon) {
        text(c, icon, x + 5, y + 40, 21, MUTED, true);
        text(c, label, x + 54, y + 17, 12f, MUTED, true);
        card(c, x + 54, y + 27, x + 346, y + 75, BORDER, Color.WHITE, 9, 1f);
        if (value > 0) {
            text(c, NumberFormat.getNumberInstance(Locale.KOREA).format(value),
                    x + 72, y + 60, 19.5f, TEXT, true);
        }
        addHit(x + 54, y + 27, x + 346, y + 75,
                () -> host.editNumber(key, label, value));
    }

'''
s = s[:start] + new_number + s[end:]

view.write_text(s, encoding='utf-8')

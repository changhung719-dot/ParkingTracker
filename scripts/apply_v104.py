from pathlib import Path
import re

root = Path('ParkingLocationPayload')

gradle = root / 'app/build.gradle'
s = gradle.read_text(encoding='utf-8')
s = re.sub(r'versionCode\s+\d+', 'versionCode 5', s)
s = re.sub(r"versionName\s+'[^']+'", "versionName '1.0.4'", s)
gradle.write_text(s, encoding='utf-8')

view = root / 'app/src/main/java/com/interfaceworld/parkinglocation/ParkingView.java'
s = view.read_text(encoding='utf-8')

# Main parking screen: fixed vertical rhythm and no overlaps.
start = s.index('    private void drawHome(Canvas c) {')
end = s.index('    private void drawVehicleCards', start)
new_home = '''    private void drawHome(Canvas c) {
        int location = prefs.getInt("selected_location", 0);
        boolean company = location == 1;

        text(c, "주차위치", 22, 29, 23, TEXT, true);
        chip(c, 22, 41, 132, 67,
                prefs.getBool("auto_detect", true) ? "● 자동 감지 ON" : "● 자동 감지 OFF",
                BLUE, LIGHT_BLUE);
        bell(c, 352, 27, true);

        text(c, "내 차량", 22, 91, 12, TEXT, true);
        drawVehicleCards(c, 22, 101, 92);

        text(c, "위치 유형", 22, 219, 12, TEXT, true);
        segment(c, 22, 229, 368, 269, new String[]{"⌂  집", "▦  회사"}, location, idx -> {
            prefs.putInt("selected_location", idx);
            int max = idx == 0 ? 5 : 2;
            if (prefs.getInt("selected_floor", 0) > max) prefs.putInt("selected_floor", max);
        });

        text(c, company ? "층 선택 (회사 주차장)" : "층 선택 (집 주차장)", 22, 295, 12, TEXT, true);
        if (company) {
            drawFloors(c, 1, 22, 307);
            card(c, 22, 351, 368, 383, Color.rgb(196, 218, 249), LIGHT_BLUE, 9, 1f);
            textCenterMiddle(c, "회사는 지하1층부터 지하3층까지만 선택할 수 있습니다.",
                    195, 367, 9.2f, BLUE, true);
        } else {
            drawFloors(c, 0, 22, 307);
        }

        button(c, 22, 394, 368, 440, "현재 주차 위치 저장", true, this::saveParking);

        text(c, "최근 저장 위치", 22, 467, 12, TEXT, true);
        drawRecentCard(c, 0, 22, 478);
        drawRecentCard(c, 1, 22, 546);

        drawBottomNav(c, 1);
    }

'''
s = s[:start] + new_home + s[end:]

# Vehicle cards: equal boxes, centered clean car image, consistent labels.
start = s.index('    private void drawVehicleCards')
end = s.index('    private void drawFloors', start)
new_cards = '''    private void drawVehicleCards(Canvas c, float x, float y, float height) {
        int selected = prefs.getInt("selected_vehicle", 0);
        float gap = 10f;
        float w = (346f - gap) / 2f;
        for (int i = 0; i < 2; i++) {
            float left = x + i * (w + gap);
            boolean on = selected == i;
            card(c, left, y, left + w, y + height,
                    on ? BLUE : BORDER, Color.WHITE, 12, on ? 1.8f : 1.1f);

            Bitmap bitmap = i == 0 ? seltos : g90;
            drawBitmapFit(c, bitmap, left + 14, y + 8, left + w - 14, y + 58);
            textCenterMiddle(c, prefs.vehicleName(i), left + w / 2f, y + 77,
                    13.2f, TEXT, true);

            circle(c, left + w - 15, y + 15, 8, on ? BLUE : Color.WHITE,
                    on ? BLUE : BORDER);
            if (on) {
                p.setColor(Color.WHITE);
                p.setStrokeWidth(1.8f);
                p.setStyle(Paint.Style.STROKE);
                Path path = new Path();
                path.moveTo(left + w - 19, y + 15);
                path.lineTo(left + w - 16, y + 18);
                path.lineTo(left + w - 11, y + 12);
                c.drawPath(path, p);
                p.setStyle(Paint.Style.FILL);
            }

            int index = i;
            addHit(left, y, left + w, y + height,
                    () -> prefs.putInt("selected_vehicle", index));
        }
    }

'''
s = s[:start] + new_cards + s[end:]

# Floor buttons remain one line and evenly spaced.
s = s.replace('float t = y + row * 43;', 'float t = y + row * 42;')
s = s.replace('smallButton(c, l, t, l + w, t + 36, labels[i], on);',
              'smallButton(c, l, t, l + w, t + 35, labels[i], on);')
s = s.replace('addHit(l, t, l + w, t + 36, () -> prefs.putInt("selected_floor", idx));',
              'addHit(l, t, l + w, t + 35, () -> prefs.putInt("selected_floor", idx));')

# Recent location cards: aligned image/text and clear text action buttons.
start = s.index('    private void drawRecentCard')
end = s.index('    private void editRecent', start)
new_recent = '''    private void drawRecentCard(Canvas c, int vehicle, float x, float y) {
        String location = prefs.getString("park_" + vehicle + "_location", "");
        String floor = prefs.getString("park_" + vehicle + "_floor", "");
        String time = prefs.getString("park_" + vehicle + "_time", "-");

        card(c, x, y, x + 346, y + 61, BORDER, Color.WHITE, 11, 1f);
        drawBitmapFit(c, vehicle == 0 ? seltos : g90,
                x + 10, y + 9, x + 88, y + 51);

        text(c, prefs.vehicleName(vehicle), x + 98, y + 21, 12.2f, TEXT, true);
        if (location.isEmpty()) {
            text(c, "저장된 위치 없음", x + 98, y + 40, 9.8f, MUTED, false);
            text(c, "-", x + 98, y + 55, 8.4f, MUTED, false);
        } else {
            text(c, (location.equals("집") ? "⌂ " : "▦ ") + location + " / " + floor,
                    x + 98, y + 40, 9.8f, BLUE, true);
            text(c, time, x + 98, y + 55, 8.4f, MUTED, false);
        }

        drawActionButton(c, x + 265, y + 13, x + 306, y + 49,
                "수정", BLUE, () -> editRecent(vehicle));
        drawActionButton(c, x + 311, y + 13, x + 344, y + 49,
                "삭제", RED, () -> deleteRecent(vehicle));
    }

    private void drawActionButton(Canvas c, float l, float t, float r, float b,
                                  String label, int color, Runnable action) {
        card(c, l, t, r, b, BORDER, Color.WHITE, 8, 1f);
        textCenterMiddle(c, label, (l + r) / 2f, (t + b) / 2f,
                9.3f, color, true);
        addHit(l, t, r, b, action);
    }

'''
s = s[:start] + new_recent + s[end:]

# Settings screen: fixed rows and clean vehicle image alignment.
start = s.index('    private void drawSettings(Canvas c) {')
end = s.index('    private void drawRegisteredVehicle', start)
new_settings = '''    private void drawSettings(Canvas c) {
        text(c, "‹", 22, 32, 32, TEXT, false);
        text(c, "자동감지 / 알림 설정", 55, 31, 19, TEXT, true);
        addHit(10, 8, 48, 50, () -> screen = Screen.HOME);

        text(c, "자동 주차 감지", 22, 79, 12, TEXT, true);
        card(c, 22, 92, 368, 160, BORDER, Color.WHITE, 12, 1f);
        bluetoothIcon(c, 48, 118);
        text(c, "차량 블루투스 연결 종료 감지", 72, 116, 12, TEXT, true);
        text(c, "등록한 차량 연결이 끊기면 주차 상태를 감지합니다.",
                72, 137, 8.9f, MUTED, false);
        toggle(c, 323, 118, prefs.getBool("auto_detect", true));
        addHit(300, 96, 360, 153,
                () -> prefs.putBool("auto_detect", !prefs.getBool("auto_detect", true)));

        text(c, "등록된 차량", 22, 187, 12, TEXT, true);
        drawRegisteredVehicle(c, 0, 22, 199);
        drawRegisteredVehicle(c, 1, 22, 264);

        text(c, "미저장 재알림", 22, 352, 12, TEXT, true);
        card(c, 22, 365, 368, 514, BORDER, Color.WHITE, 12, 1f);
        bell(c, 49, 395, false);
        text(c, "주차 위치가 저장되지 않으면", 73, 392, 12, TEXT, true);
        text(c, "알림을 다시 보내드립니다.", 73, 412, 10, MUTED, false);
        toggle(c, 323, 395, prefs.getBool("reminder", true));
        addHit(300, 370, 360, 430,
                () -> prefs.putBool("reminder", !prefs.getBool("reminder", true)));

        text(c, "재알림 시간", 42, 459, 10, MUTED, false);
        card(c, 142, 438, 348, 478, BORDER, BG, 8, 1f);
        text(c, "2분 후 알림", 158, 464, 11, TEXT, true);
        text(c, "⌄", 327, 465, 14, MUTED, false);
        card(c, 42, 487, 348, 507, Color.TRANSPARENT, LIGHT_BLUE, 6, 0f);
        textCenterMiddle(c, "ⓘ  저장하지 않으면 2분 후 다시 알려줍니다.",
                195, 497, 8.8f, BLUE, false);

        button(c, 22, 542, 368, 588, "테스트 알림 보내기", false, host::testNotification);
        button(c, 22, 598, 368, 646, "설정 저장", true,
                () -> host.showMessage("자동감지와 알림 설정을 저장했습니다."));
        drawBottomNav(c, 3);
    }

'''
s = s[:start] + new_settings + s[end:]

start = s.index('    private void drawRegisteredVehicle')
end = s.index('    private void drawVehicle(Canvas c)', start)
new_registered = '''    private void drawRegisteredVehicle(Canvas c, int vehicle, float x, float y) {
        card(c, x, y, x + 346, y + 56, BORDER, Color.WHITE, 10, 1f);
        drawBitmapFit(c, vehicle == 0 ? seltos : g90,
                x + 12, y + 7, x + 104, y + 49);
        textCenterMiddle(c, prefs.vehicleName(vehicle), x + 140, y + 28,
                12.5f, TEXT, true);

        String bluetoothName = prefs.getString("bt_name_" + vehicle, "");
        chip(c, x + 276, y + 14, x + 334, y + 42,
                bluetoothName.isEmpty() ? "등록" : "등록됨", BLUE, LIGHT_BLUE);
        addHit(x, y, x + 346, y + 56, () -> host.chooseBluetoothDevice(vehicle));
    }

'''
s = s[:start] + new_registered + s[end:]

# Consistent vertical centering for all segmented and main buttons.
s = s.replace('float top = 746;', 'float top = 744;')
s = s.replace(
    'textCenter(c, labels[i], a + w / 2, (t + b) / 2 + 5, 13, selected == i ? Color.WHITE : TEXT, true);',
    'textCenterMiddle(c, labels[i], a + w / 2, (t + b) / 2, 13, selected == i ? Color.WHITE : TEXT, true);')
s = s.replace(
    'textCenter(c, label, (l + r) / 2, (t + b) / 2 + 5, 13, primary ? Color.WHITE : BLUE, true);',
    'textCenterMiddle(c, label, (l + r) / 2, (t + b) / 2, 13, primary ? Color.WHITE : BLUE, true);')

view.write_text(s, encoding='utf-8')

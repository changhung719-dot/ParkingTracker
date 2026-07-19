from pathlib import Path
import re

root = Path('ParkingLocationPayload')

gradle = root / 'app/build.gradle'
s = gradle.read_text(encoding='utf-8')
s = re.sub(r'versionCode\s+\d+', 'versionCode 7', s)
s = re.sub(r"versionName\s+'[^']+'", "versionName '1.0.7'", s)
s = re.sub(r'^\s*signingConfig signingConfigs\.debug\s*\n', '', s, flags=re.M)
gradle.write_text(s, encoding='utf-8')

view = root / 'app/src/main/java/com/interfaceworld/parkinglocation/ParkingView.java'
s = view.read_text(encoding='utf-8')

# Parking screen: distribute all blocks vertically like the engine-oil screen.
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
        drawVehicleCards(c, 22, 101, 96);

        text(c, "위치 유형", 22, 221, 12, TEXT, true);
        segment(c, 22, 231, 368, 271, new String[]{"⌂  집", "▦  회사"}, location, idx -> {
            prefs.putInt("selected_location", idx);
            int max = idx == 0 ? 5 : 2;
            if (prefs.getInt("selected_floor", 0) > max) prefs.putInt("selected_floor", max);
        });

        text(c, company ? "층 선택 (회사 주차장)" : "층 선택 (집 주차장)", 22, 297, 12, TEXT, true);
        if (company) {
            drawFloors(c, 1, 22, 309);
            card(c, 22, 352, 368, 384, Color.rgb(196, 218, 249), LIGHT_BLUE, 9, 1f);
            textCenterMiddle(c, "회사는 지하1층부터 지하3층까지만 선택할 수 있습니다.",
                    195, 368, 9.2f, BLUE, true);
        } else {
            drawFloors(c, 0, 22, 309);
        }

        button(c, 22, 402, 368, 450, "현재 주차 위치 저장", true, this::saveParking);

        text(c, "최근 저장 위치", 22, 482, 12, TEXT, true);
        drawRecentCard(c, 0, 22, 500);
        drawRecentCard(c, 1, 22, 608);

        drawBottomNav(c, 1);
    }

'''
s = s[:start] + new_home + s[end:]

# Main car cards: keep the full vehicle visible with generous padding and true aspect ratio.
start = s.index('    private void drawVehicleCards')
end = s.index('    private void drawFloors', start)
new_vehicle_cards = '''    private void drawVehicleCards(Canvas c, float x, float y, float height) {
        int selected = prefs.getInt("selected_vehicle", 0);
        float gap = 10f;
        float w = (346f - gap) / 2f;
        for (int i = 0; i < 2; i++) {
            float left = x + i * (w + gap);
            boolean on = selected == i;
            card(c, left, y, left + w, y + height,
                    on ? BLUE : BORDER, Color.WHITE, 12, on ? 1.8f : 1.1f);

            Bitmap bitmap = i == 0 ? seltos : g90;
            drawBitmapFit(c, bitmap, left + 12, y + 9, left + w - 12, y + 64);
            textCenterMiddle(c, prefs.vehicleName(i), left + w / 2f, y + 81,
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
s = s[:start] + new_vehicle_cards + s[end:]

# Recent cards are taller and fill the lower page without a dead zone.
start = s.index('    private void drawRecentCard')
end = s.index('    private void editRecent', start)
new_recent = '''    private void drawRecentCard(Canvas c, int vehicle, float x, float y) {
        String location = prefs.getString("park_" + vehicle + "_location", "");
        String floor = prefs.getString("park_" + vehicle + "_floor", "");
        String time = prefs.getString("park_" + vehicle + "_time", "-");

        card(c, x, y, x + 346, y + 88, BORDER, Color.WHITE, 12, 1f);
        drawBitmapFit(c, vehicle == 0 ? seltos : g90,
                x + 12, y + 13, x + 104, y + 74);

        text(c, prefs.vehicleName(vehicle), x + 112, y + 28, 12.6f, TEXT, true);
        if (location.isEmpty()) {
            text(c, "저장된 위치 없음", x + 112, y + 50, 10.2f, MUTED, false);
            text(c, "-", x + 112, y + 70, 8.8f, MUTED, false);
        } else {
            text(c, (location.equals("집") ? "⌂ " : "▦ ") + location + " / " + floor,
                    x + 112, y + 51, 10.2f, BLUE, true);
            text(c, time, x + 112, y + 72, 8.8f, MUTED, false);
        }

        drawActionButton(c, x + 263, y + 22, x + 307, y + 66,
                "수정", BLUE, () -> editRecent(vehicle));
        drawActionButton(c, x + 312, y + 22, x + 344, y + 66,
                "삭제", RED, () -> deleteRecent(vehicle));
    }

    private void drawActionButton(Canvas c, float l, float t, float r, float b,
                                  String label, int color, Runnable action) {
        card(c, l, t, r, b, BORDER, Color.WHITE, 8, 1f);
        textCenterMiddle(c, label, (l + r) / 2f, (t + b) / 2f,
                9.5f, color, true);
        addHit(l, t, r, b, action);
    }

'''
s = s[:start] + new_recent + s[end:]

# Settings screen: evenly fill the page, matching the engine-oil layout rhythm.
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
        drawRegisteredVehicle(c, 1, 22, 269);

        text(c, "미저장 재알림", 22, 350, 12, TEXT, true);
        card(c, 22, 363, 368, 536, BORDER, Color.WHITE, 12, 1f);
        bell(c, 49, 398, false);
        text(c, "주차 위치가 저장되지 않으면", 73, 395, 12, TEXT, true);
        text(c, "알림을 다시 보내드립니다.", 73, 417, 10, MUTED, false);
        toggle(c, 323, 398, prefs.getBool("reminder", true));
        addHit(300, 370, 360, 435,
                () -> prefs.putBool("reminder", !prefs.getBool("reminder", true)));

        text(c, "재알림 시간", 42, 470, 10, MUTED, false);
        card(c, 142, 446, 348, 490, BORDER, BG, 8, 1f);
        text(c, "2분 후 알림", 158, 474, 11, TEXT, true);
        text(c, "⌄", 327, 475, 14, MUTED, false);
        card(c, 42, 505, 348, 529, Color.TRANSPARENT, LIGHT_BLUE, 6, 0f);
        textCenterMiddle(c, "ⓘ  저장하지 않으면 2분 후 다시 알려줍니다.",
                195, 517, 8.8f, BLUE, false);

        button(c, 22, 566, 368, 616, "테스트 알림 보내기", false, host::testNotification);
        button(c, 22, 632, 368, 700, "설정 저장", true,
                () -> host.showMessage("자동감지와 알림 설정을 저장했습니다."));
        drawBottomNav(c, 3);
    }

'''
s = s[:start] + new_settings + s[end:]

start = s.index('    private void drawRegisteredVehicle')
end = s.index('    private void drawVehicle(Canvas c)', start)
new_registered = '''    private void drawRegisteredVehicle(Canvas c, int vehicle, float x, float y) {
        card(c, x, y, x + 346, y + 60, BORDER, Color.WHITE, 10, 1f);
        drawBitmapFit(c, vehicle == 0 ? seltos : g90,
                x + 12, y + 8, x + 116, y + 52);
        textCenterMiddle(c, prefs.vehicleName(vehicle), x + 147, y + 30,
                12.5f, TEXT, true);

        String bluetoothName = prefs.getString("bt_name_" + vehicle, "");
        chip(c, x + 276, y + 16, x + 334, y + 44,
                bluetoothName.isEmpty() ? "등록" : "등록됨", BLUE, LIGHT_BLUE);
        addHit(x, y, x + 346, y + 60, () -> host.chooseBluetoothDevice(vehicle));
    }

'''
s = s[:start] + new_registered + s[end:]

view.write_text(s, encoding='utf-8')

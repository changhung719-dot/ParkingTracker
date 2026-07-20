from pathlib import Path
import re

root = Path('ParkingLocationPayload')

gradle = root / 'app/build.gradle'
s = gradle.read_text(encoding='utf-8')
s = re.sub(r'versionCode\s+\d+', 'versionCode 10', s)
s = re.sub(r"versionName\s+'[^']+'", "versionName '1.0.10'", s)
s = re.sub(r'^\s*signingConfig signingConfigs\.debug\s*\n', '', s, flags=re.M)
gradle.write_text(s, encoding='utf-8')

view = root / 'app/src/main/java/com/interfaceworld/parkinglocation/ParkingView.java'
s = view.read_text(encoding='utf-8')

# Keep all positions and functions from v1.0.9. Only enlarge/strengthen typography
# and replace the simplified vehicle drawing with official photo resources.
start = s.index('    private void drawHome(Canvas c) {')
end = s.index('    private void drawVehicleCards', start)
new_home = '''    private void drawHome(Canvas c) {
        int location = prefs.getInt("selected_location", 0);
        boolean company = location == 1;

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
            int max = idx == 0 ? 5 : 2;
            if (prefs.getInt("selected_floor", 0) > max) prefs.putInt("selected_floor", max);
        });

        text(c, company ? "층 선택 (회사 주차장)" : "층 선택 (집 주차장)",
                22, 329, 15.5f, TEXT, true);
        if (company) {
            drawFloors(c, 1, 22, 342);
            card(c, 22, 390, 368, 426, Color.rgb(196, 218, 249), LIGHT_BLUE, 9, 1f);
            textCenterMiddle(c, "회사는 지하1층부터 지하3층까지만 선택할 수 있습니다.",
                    195, 408, 10.8f, BLUE, true);
        } else {
            drawFloors(c, 0, 22, 342);
        }

        button(c, 22, 440, 368, 495, "현재 주차 위치 저장", true, this::saveParking);

        text(c, "최근 저장 위치", 22, 526, 15.5f, TEXT, true);
        drawRecentCard(c, 0, 22, 541);
        drawRecentCard(c, 1, 22, 634);

        drawBottomNav(c, 1);
    }

'''
s = s[:start] + new_home + s[end:]

start = s.index('    private void drawVehicleCards')
end = s.index('    private void drawVehicleIllustration', start)
new_vehicle_cards = '''    private void drawVehicleCards(Canvas c, float x, float y, float height) {
        int selected = prefs.getInt("selected_vehicle", 0);
        float gap = 10f;
        float w = (346f - gap) / 2f;
        for (int i = 0; i < 2; i++) {
            float left = x + i * (w + gap);
            boolean on = selected == i;
            card(c, left, y, left + w, y + height,
                    on ? BLUE : BORDER, Color.WHITE, 12, on ? 1.8f : 1.1f);

            drawVehicleIllustration(c, i, left + 10, y + 8, left + w - 10, y + 75);
            textCenterMiddle(c, prefs.vehicleName(i), left + w / 2f, y + 95,
                    16.5f, TEXT, true);

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

start = s.index('    private void drawVehicleIllustration')
end = s.index('    private void drawFloors', start)
new_photo_method = '''    private void drawVehicleIllustration(Canvas c, int vehicle, float l, float t, float r, float b) {
        Bitmap bitmap = vehicle == 0 ? seltos : g90;
        drawBitmapFit(c, bitmap, l, t, r, b);
    }

'''
s = s[:start] + new_photo_method + s[end:]

start = s.index('    private void drawRecentCard')
end = s.index('    private void editRecent', start)
new_recent = '''    private void drawRecentCard(Canvas c, int vehicle, float x, float y) {
        String location = prefs.getString("park_" + vehicle + "_location", "");
        String floor = prefs.getString("park_" + vehicle + "_floor", "");
        String time = prefs.getString("park_" + vehicle + "_time", "-");

        card(c, x, y, x + 346, y + 84, BORDER, Color.WHITE, 12, 1f);
        drawVehicleIllustration(c, vehicle, x + 9, y + 10, x + 116, y + 74);

        text(c, prefs.vehicleName(vehicle), x + 120, y + 28, 16f, TEXT, true);
        if (location.isEmpty()) {
            text(c, "저장된 위치 없음", x + 120, y + 51, 12.7f, MUTED, true);
            text(c, "-", x + 120, y + 72, 10.8f, MUTED, true);
        } else {
            text(c, (location.equals("집") ? "⌂ " : "▦ ") + location + " / " + floor,
                    x + 120, y + 51, 12.7f, BLUE, true);
            text(c, time, x + 120, y + 72, 10.8f, MUTED, true);
        }

        drawActionButton(c, x + 266, y + 18, x + 309, y + 66,
                "수정", BLUE, () -> editRecent(vehicle));
        drawActionButton(c, x + 314, y + 18, x + 344, y + 66,
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

start = s.index('    private void drawSettings(Canvas c) {')
end = s.index('    private void drawRegisteredVehicle', start)
new_settings = '''    private void drawSettings(Canvas c) {
        text(c, "‹", 22, 34, 35, TEXT, true);
        text(c, "자동감지 / 알림 설정", 55, 33, 23f, TEXT, true);
        addHit(10, 8, 48, 54, () -> screen = Screen.HOME);

        text(c, "자동 주차 감지", 22, 84, 15f, TEXT, true);
        card(c, 22, 96, 368, 181, BORDER, Color.WHITE, 12, 1f);
        bluetoothIcon(c, 48, 128);
        text(c, "차량 블루투스 연결 종료 감지", 72, 124, 14f, TEXT, true);
        text(c, "등록한 차량 연결이 끊기면 주차 상태를 감지합니다.",
                72, 148, 10.4f, MUTED, true);
        toggle(c, 323, 128, prefs.getBool("auto_detect", true));
        addHit(300, 100, 360, 176,
                () -> prefs.putBool("auto_detect", !prefs.getBool("auto_detect", true)));

        text(c, "등록된 차량", 22, 211, 15f, TEXT, true);
        drawRegisteredVehicle(c, 0, 22, 224);
        drawRegisteredVehicle(c, 1, 22, 305);

        text(c, "미저장 재알림", 22, 405, 15f, TEXT, true);
        card(c, 22, 418, 368, 594, BORDER, Color.WHITE, 12, 1f);
        bell(c, 49, 454, false);
        text(c, "주차 위치가 저장되지 않으면", 73, 449, 14f, TEXT, true);
        text(c, "알림을 다시 보내드립니다.", 73, 473, 11.7f, MUTED, true);
        toggle(c, 323, 454, prefs.getBool("reminder", true));
        addHit(300, 424, 360, 492,
                () -> prefs.putBool("reminder", !prefs.getBool("reminder", true)));

        text(c, "재알림 시간", 42, 526, 11.8f, MUTED, true);
        card(c, 142, 500, 348, 548, BORDER, BG, 8, 1f);
        text(c, "2분 후 알림", 158, 531, 13f, TEXT, true);
        text(c, "⌄", 327, 532, 15, MUTED, true);
        card(c, 42, 558, 348, 584, Color.TRANSPARENT, LIGHT_BLUE, 6, 0f);
        textCenterMiddle(c, "ⓘ  저장하지 않으면 2분 후 다시 알려줍니다.",
                195, 571, 10.1f, BLUE, true);

        button(c, 22, 616, 368, 666, "테스트 알림 보내기", false, host::testNotification);
        button(c, 22, 678, 368, 724, "설정 저장", true,
                () -> host.showMessage("자동감지와 알림 설정을 저장했습니다."));
        drawBottomNav(c, 3);
    }

'''
s = s[:start] + new_settings + s[end:]

start = s.index('    private void drawRegisteredVehicle')
end = s.index('    private void drawVehicle(Canvas c)', start)
new_registered = '''    private void drawRegisteredVehicle(Canvas c, int vehicle, float x, float y) {
        card(c, x, y, x + 346, y + 70, BORDER, Color.WHITE, 11, 1f);
        drawVehicleIllustration(c, vehicle, x + 10, y + 7, x + 128, y + 63);
        textCenterMiddle(c, prefs.vehicleName(vehicle), x + 171, y + 35,
                15.5f, TEXT, true);

        String bluetoothName = prefs.getString("bt_name_" + vehicle, "");
        chip(c, x + 276, y + 20, x + 334, y + 50,
                bluetoothName.isEmpty() ? "등록" : "등록됨", BLUE, LIGHT_BLUE);
        addHit(x, y, x + 346, y + 70, () -> host.chooseBluetoothDevice(vehicle));
    }

'''
s = s[:start] + new_registered + s[end:]

# Make normal text slightly thicker without changing logic or layout.
s = s.replace('Typeface.create("sans-serif", Typeface.NORMAL)',
              'Typeface.create("sans-serif-medium", Typeface.NORMAL)')

# Slightly larger shared labels only; geometry and hit targets remain unchanged.
s = re.sub(
    r'textCenterMiddle\(c, labels\[i\], a \+ w / 2, \(t \+ b\) / 2, [0-9.]+f?, selected == i \? Color\.WHITE : TEXT, true\);',
    'textCenterMiddle(c, labels[i], a + w / 2, (t + b) / 2, 15.3f, selected == i ? Color.WHITE : TEXT, true);',
    s)
s = re.sub(
    r'textCenterMiddle\(c, label, \(l \+ r\) / 2, \(t \+ b\) / 2, [0-9.]+f?, primary \? Color\.WHITE : BLUE, true\);',
    'textCenterMiddle(c, label, (l + r) / 2, (t + b) / 2, 15.5f, primary ? Color.WHITE : BLUE, true);',
    s)
s = s.replace('float size = label.length() >= 5 ? 12.0f : 13.0f;',
              'float size = label.length() >= 5 ? 12.8f : 13.8f;')

view.write_text(s, encoding='utf-8')

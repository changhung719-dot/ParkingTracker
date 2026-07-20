from pathlib import Path
import re

root = Path('ParkingLocationPayload')

# Android update version.
gradle = root / 'app/build.gradle'
s = gradle.read_text(encoding='utf-8')
s = re.sub(r'versionCode\s+\d+', 'versionCode 9', s)
s = re.sub(r"versionName\s+'[^']+'", "versionName '1.0.9'", s)
s = re.sub(r'^\s*signingConfig signingConfigs\.debug\s*\n', '', s, flags=re.M)
gradle.write_text(s, encoding='utf-8')

view = root / 'app/src/main/java/com/interfaceworld/parkinglocation/ParkingView.java'
s = view.read_text(encoding='utf-8')

# Fill the entire usable screen above the fixed bottom navigation and enlarge text.
start = s.index('    private void drawHome(Canvas c) {')
end = s.index('    private void drawVehicleCards', start)
new_home = '''    private void drawHome(Canvas c) {
        int location = prefs.getInt("selected_location", 0);
        boolean company = location == 1;

        text(c, "주차위치", 22, 31, 27, TEXT, true);
        chip(c, 22, 44, 142, 73,
                prefs.getBool("auto_detect", true) ? "● 자동 감지 ON" : "● 자동 감지 OFF",
                BLUE, LIGHT_BLUE);
        bell(c, 352, 29, true);

        text(c, "내 차량", 22, 99, 14.5f, TEXT, true);
        drawVehicleCards(c, 22, 110, 108);

        text(c, "위치 유형", 22, 243, 14.5f, TEXT, true);
        segment(c, 22, 254, 368, 302, new String[]{"⌂  집", "▦  회사"}, location, idx -> {
            prefs.putInt("selected_location", idx);
            int max = idx == 0 ? 5 : 2;
            if (prefs.getInt("selected_floor", 0) > max) prefs.putInt("selected_floor", max);
        });

        text(c, company ? "층 선택 (회사 주차장)" : "층 선택 (집 주차장)",
                22, 329, 14.5f, TEXT, true);
        if (company) {
            drawFloors(c, 1, 22, 342);
            card(c, 22, 390, 368, 426, Color.rgb(196, 218, 249), LIGHT_BLUE, 9, 1f);
            textCenterMiddle(c, "회사는 지하1층부터 지하3층까지만 선택할 수 있습니다.",
                    195, 408, 10.3f, BLUE, true);
        } else {
            drawFloors(c, 0, 22, 342);
        }

        button(c, 22, 440, 368, 495, "현재 주차 위치 저장", true, this::saveParking);

        text(c, "최근 저장 위치", 22, 526, 14.5f, TEXT, true);
        drawRecentCard(c, 0, 22, 541);
        drawRecentCard(c, 1, 22, 634);

        drawBottomNav(c, 1);
    }

'''
s = s[:start] + new_home + s[end:]

# Keep the same Seltos/G90 vector artwork, only center it inside taller cards.
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

            drawVehicleIllustration(c, i, left + 13, y + 9, left + w - 13, y + 74);
            textCenterMiddle(c, prefs.vehicleName(i), left + w / 2f, y + 94,
                    15.5f, TEXT, true);

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

# Larger floor buttons and labels while preserving all home/company floor rules.
s = s.replace('float t = y + row * 42;', 'float t = y + row * 46;')
s = s.replace('smallButton(c, l, t, l + w, t + 35, labels[i], on);',
              'smallButton(c, l, t, l + w, t + 40, labels[i], on);')
s = s.replace('addHit(l, t, l + w, t + 35, () -> prefs.putInt("selected_floor", idx));',
              'addHit(l, t, l + w, t + 40, () -> prefs.putInt("selected_floor", idx));')
s = s.replace('float size = label.length() >= 5 ? 10.8f : 11.8f;',
              'float size = label.length() >= 5 ? 12.0f : 13.0f;')

# Larger recent-location cards positioned close to the navigation bar.
start = s.index('    private void drawRecentCard')
end = s.index('    private void editRecent', start)
new_recent = '''    private void drawRecentCard(Canvas c, int vehicle, float x, float y) {
        String location = prefs.getString("park_" + vehicle + "_location", "");
        String floor = prefs.getString("park_" + vehicle + "_floor", "");
        String time = prefs.getString("park_" + vehicle + "_time", "-");

        card(c, x, y, x + 346, y + 84, BORDER, Color.WHITE, 12, 1f);
        drawVehicleIllustration(c, vehicle, x + 12, y + 13, x + 112, y + 72);

        text(c, prefs.vehicleName(vehicle), x + 118, y + 28, 15f, TEXT, true);
        if (location.isEmpty()) {
            text(c, "저장된 위치 없음", x + 118, y + 51, 12.1f, MUTED, false);
            text(c, "-", x + 118, y + 72, 10.3f, MUTED, false);
        } else {
            text(c, (location.equals("집") ? "⌂ " : "▦ ") + location + " / " + floor,
                    x + 118, y + 51, 12.1f, BLUE, true);
            text(c, time, x + 118, y + 72, 10.3f, MUTED, false);
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
                10.5f, color, true);
        addHit(l, t, r, b, action);
    }

'''
s = s[:start] + new_recent + s[end:]

# Settings screen also fills the usable height and uses larger text.
start = s.index('    private void drawSettings(Canvas c) {')
end = s.index('    private void drawRegisteredVehicle', start)
new_settings = '''    private void drawSettings(Canvas c) {
        text(c, "‹", 22, 34, 34, TEXT, false);
        text(c, "자동감지 / 알림 설정", 55, 33, 21.5f, TEXT, true);
        addHit(10, 8, 48, 54, () -> screen = Screen.HOME);

        text(c, "자동 주차 감지", 22, 84, 13.8f, TEXT, true);
        card(c, 22, 96, 368, 181, BORDER, Color.WHITE, 12, 1f);
        bluetoothIcon(c, 48, 128);
        text(c, "차량 블루투스 연결 종료 감지", 72, 124, 13.2f, TEXT, true);
        text(c, "등록한 차량 연결이 끊기면 주차 상태를 감지합니다.",
                72, 148, 9.8f, MUTED, false);
        toggle(c, 323, 128, prefs.getBool("auto_detect", true));
        addHit(300, 100, 360, 176,
                () -> prefs.putBool("auto_detect", !prefs.getBool("auto_detect", true)));

        text(c, "등록된 차량", 22, 211, 13.8f, TEXT, true);
        drawRegisteredVehicle(c, 0, 22, 224);
        drawRegisteredVehicle(c, 1, 22, 305);

        text(c, "미저장 재알림", 22, 405, 13.8f, TEXT, true);
        card(c, 22, 418, 368, 594, BORDER, Color.WHITE, 12, 1f);
        bell(c, 49, 454, false);
        text(c, "주차 위치가 저장되지 않으면", 73, 449, 13.2f, TEXT, true);
        text(c, "알림을 다시 보내드립니다.", 73, 473, 11f, MUTED, false);
        toggle(c, 323, 454, prefs.getBool("reminder", true));
        addHit(300, 424, 360, 492,
                () -> prefs.putBool("reminder", !prefs.getBool("reminder", true)));

        text(c, "재알림 시간", 42, 526, 11f, MUTED, false);
        card(c, 142, 500, 348, 548, BORDER, BG, 8, 1f);
        text(c, "2분 후 알림", 158, 531, 12.2f, TEXT, true);
        text(c, "⌄", 327, 532, 15, MUTED, false);
        card(c, 42, 558, 348, 584, Color.TRANSPARENT, LIGHT_BLUE, 6, 0f);
        textCenterMiddle(c, "ⓘ  저장하지 않으면 2분 후 다시 알려줍니다.",
                195, 571, 9.6f, BLUE, false);

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
        drawVehicleIllustration(c, vehicle, x + 13, y + 10, x + 124, y + 59);
        textCenterMiddle(c, prefs.vehicleName(vehicle), x + 166, y + 35,
                14.2f, TEXT, true);

        String bluetoothName = prefs.getString("bt_name_" + vehicle, "");
        chip(c, x + 276, y + 20, x + 334, y + 50,
                bluetoothName.isEmpty() ? "등록" : "등록됨", BLUE, LIGHT_BLUE);
        addHit(x, y, x + 346, y + 70, () -> host.chooseBluetoothDevice(vehicle));
    }

'''
s = s[:start] + new_registered + s[end:]

# Larger common segment/button typography.
s = re.sub(
    r'textCenterMiddle\(c, labels\[i\], a \+ w / 2, \(t \+ b\) / 2, [0-9.]+f?, selected == i \? Color\.WHITE : TEXT, true\);',
    'textCenterMiddle(c, labels[i], a + w / 2, (t + b) / 2, 14.2f, selected == i ? Color.WHITE : TEXT, true);',
    s)
s = re.sub(
    r'textCenterMiddle\(c, label, \(l \+ r\) / 2, \(t \+ b\) / 2, [0-9.]+f?, primary \? Color\.WHITE : BLUE, true\);',
    'textCenterMiddle(c, label, (l + r) / 2, (t + b) / 2, 14.5f, primary ? Color.WHITE : BLUE, true);',
    s)

# Bottom navigation keeps the same position but uses more readable labels.
start = s.index('    private void drawBottomNav(Canvas c, int selected) {')
end = s.index('    private interface SegmentListener', start)
new_nav = '''    private void drawBottomNav(Canvas c, int selected) {
        float top = 742f;
        p.setColor(Color.WHITE);
        p.setShadowLayer(8, 0, -2, Color.argb(35, 30, 60, 100));
        c.drawRect(0, top, DW, DH, p);
        p.clearShadowLayer();

        String[] labels = {"홈", "주차", "차량", "설정"};
        String[] icons = {"⌂", "P", "▰", "⚙"};
        for (int i = 0; i < 4; i++) {
            float cx = 49 + i * 97.3f;
            int color = i == selected ? BLUE : MUTED;
            textCenter(c, icons[i], cx, 772, 22, color, true);
            textCenter(c, labels[i], cx, 797, 11.5f, color, i == selected);
            int idx = i;
            addHit(cx - 45, top, cx + 45, DH, () -> {
                if (idx == 0) screen = Screen.HOME;
                else if (idx == 1) screen = Screen.PARKING;
                else if (idx == 2) screen = Screen.VEHICLE;
                else screen = Screen.SETTINGS;
            });
        }
    }

'''
s = s[:start] + new_nav + s[end:]

view.write_text(s, encoding='utf-8')

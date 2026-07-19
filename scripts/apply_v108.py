from pathlib import Path
import re

root = Path('ParkingLocationPayload')

# Increment the Android package version so the phone accepts it as an update.
gradle = root / 'app/build.gradle'
s = gradle.read_text(encoding='utf-8')
s = re.sub(r'versionCode\s+\d+', 'versionCode 8', s)
s = re.sub(r"versionName\s+'[^']+'", "versionName '1.0.8'", s)
s = re.sub(r'^\s*signingConfig signingConfigs\.debug\s*\n', '', s, flags=re.M)
gradle.write_text(s, encoding='utf-8')

view = root / 'app/src/main/java/com/interfaceworld/parkinglocation/ParkingView.java'
s = view.read_text(encoding='utf-8')

# Parking screen: slightly larger fonts, still kept on a single screen.
start = s.index('    private void drawHome(Canvas c) {')
end = s.index('    private void drawVehicleCards', start)
new_home = '''    private void drawHome(Canvas c) {
        int location = prefs.getInt("selected_location", 0);
        boolean company = location == 1;

        text(c, "주차위치", 22, 30, 25, TEXT, true);
        chip(c, 22, 42, 136, 69,
                prefs.getBool("auto_detect", true) ? "● 자동 감지 ON" : "● 자동 감지 OFF",
                BLUE, LIGHT_BLUE);
        bell(c, 352, 28, true);

        text(c, "내 차량", 22, 92, 13.2f, TEXT, true);
        drawVehicleCards(c, 22, 102, 96);

        text(c, "위치 유형", 22, 222, 13.2f, TEXT, true);
        segment(c, 22, 232, 368, 273, new String[]{"⌂  집", "▦  회사"}, location, idx -> {
            prefs.putInt("selected_location", idx);
            int max = idx == 0 ? 5 : 2;
            if (prefs.getInt("selected_floor", 0) > max) prefs.putInt("selected_floor", max);
        });

        text(c, company ? "층 선택 (회사 주차장)" : "층 선택 (집 주차장)", 22, 299, 13.2f, TEXT, true);
        if (company) {
            drawFloors(c, 1, 22, 311);
            card(c, 22, 354, 368, 386, Color.rgb(196, 218, 249), LIGHT_BLUE, 9, 1f);
            textCenterMiddle(c, "회사는 지하1층부터 지하3층까지만 선택할 수 있습니다.",
                    195, 370, 9.6f, BLUE, true);
        } else {
            drawFloors(c, 0, 22, 311);
        }

        button(c, 22, 403, 368, 451, "현재 주차 위치 저장", true, this::saveParking);

        text(c, "최근 저장 위치", 22, 483, 13.2f, TEXT, true);
        drawRecentCard(c, 0, 22, 501);
        drawRecentCard(c, 1, 22, 609);

        drawBottomNav(c, 1);
    }

'''
s = s[:start] + new_home + s[end:]

# Vehicle cards use a complete vector illustration instead of a clipped bitmap.
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

            drawVehicleIllustration(c, i, left + 13, y + 8, left + w - 13, y + 66);
            textCenterMiddle(c, prefs.vehicleName(i), left + w / 2f, y + 82,
                    14f, TEXT, true);

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

    private void drawVehicleIllustration(Canvas c, int vehicle, float l, float t, float r, float b) {
        float w = r - l;
        float h = b - t;
        float wheelY = t + h * 0.76f;
        float wheelRadius = Math.max(5.5f, h * 0.14f);
        float frontWheelX = l + w * 0.25f;
        float rearWheelX = l + w * 0.76f;

        // Wheels are drawn first so the complete tyre remains visible.
        p.setStyle(Paint.Style.FILL);
        p.setColor(Color.rgb(30, 34, 40));
        c.drawCircle(frontWheelX, wheelY, wheelRadius, p);
        c.drawCircle(rearWheelX, wheelY, wheelRadius, p);
        p.setColor(Color.rgb(135, 145, 158));
        c.drawCircle(frontWheelX, wheelY, wheelRadius * 0.48f, p);
        c.drawCircle(rearWheelX, wheelY, wheelRadius * 0.48f, p);
        p.setColor(Color.rgb(230, 235, 241));
        c.drawCircle(frontWheelX, wheelY, wheelRadius * 0.22f, p);
        c.drawCircle(rearWheelX, wheelY, wheelRadius * 0.22f, p);

        if (vehicle == 0) {
            // Seltos: taller white SUV silhouette.
            Path body = new Path();
            body.moveTo(l + w * 0.05f, t + h * 0.65f);
            body.lineTo(l + w * 0.12f, t + h * 0.42f);
            body.lineTo(l + w * 0.30f, t + h * 0.34f);
            body.lineTo(l + w * 0.42f, t + h * 0.16f);
            body.lineTo(l + w * 0.72f, t + h * 0.16f);
            body.lineTo(l + w * 0.88f, t + h * 0.34f);
            body.lineTo(l + w * 0.96f, t + h * 0.55f);
            body.lineTo(l + w * 0.94f, t + h * 0.73f);
            body.lineTo(l + w * 0.05f, t + h * 0.73f);
            body.close();
            p.setColor(Color.rgb(248, 249, 250));
            p.setStyle(Paint.Style.FILL);
            c.drawPath(body, p);
            p.setStyle(Paint.Style.STROKE);
            p.setStrokeWidth(1.2f);
            p.setColor(Color.rgb(150, 160, 172));
            c.drawPath(body, p);

            Path windows = new Path();
            windows.moveTo(l + w * 0.34f, t + h * 0.36f);
            windows.lineTo(l + w * 0.45f, t + h * 0.20f);
            windows.lineTo(l + w * 0.69f, t + h * 0.20f);
            windows.lineTo(l + w * 0.82f, t + h * 0.36f);
            windows.close();
            p.setStyle(Paint.Style.FILL);
            p.setColor(Color.rgb(49, 62, 77));
            c.drawPath(windows, p);
            p.setStyle(Paint.Style.STROKE);
            p.setStrokeWidth(1f);
            p.setColor(Color.rgb(110, 125, 140));
            c.drawLine(l + w * 0.56f, t + h * 0.20f, l + w * 0.56f, t + h * 0.36f, p);

            p.setStyle(Paint.Style.FILL);
            p.setColor(Color.rgb(35, 42, 48));
            c.drawRoundRect(new RectF(l + w * 0.08f, t + h * 0.50f,
                    l + w * 0.27f, t + h * 0.64f), 3f, 3f, p);
            p.setColor(Color.rgb(206, 216, 226));
            c.drawRoundRect(new RectF(l + w * 0.80f, t + h * 0.47f,
                    l + w * 0.94f, t + h * 0.54f), 2f, 2f, p);
            p.setColor(Color.rgb(55, 62, 68));
            c.drawRect(l + w * 0.08f, t + h * 0.69f, l + w * 0.92f, t + h * 0.75f, p);
        } else {
            // G90: longer, lower black luxury sedan silhouette.
            Path body = new Path();
            body.moveTo(l + w * 0.04f, t + h * 0.66f);
            body.lineTo(l + w * 0.11f, t + h * 0.48f);
            body.lineTo(l + w * 0.31f, t + h * 0.40f);
            body.lineTo(l + w * 0.43f, t + h * 0.24f);
            body.lineTo(l + w * 0.69f, t + h * 0.24f);
            body.lineTo(l + w * 0.84f, t + h * 0.40f);
            body.lineTo(l + w * 0.96f, t + h * 0.53f);
            body.lineTo(l + w * 0.95f, t + h * 0.72f);
            body.lineTo(l + w * 0.04f, t + h * 0.72f);
            body.close();
            p.setStyle(Paint.Style.FILL);
            p.setColor(Color.rgb(20, 24, 30));
            c.drawPath(body, p);
            p.setStyle(Paint.Style.STROKE);
            p.setStrokeWidth(1.2f);
            p.setColor(Color.rgb(95, 106, 120));
            c.drawPath(body, p);

            Path windows = new Path();
            windows.moveTo(l + w * 0.35f, t + h * 0.41f);
            windows.lineTo(l + w * 0.46f, t + h * 0.27f);
            windows.lineTo(l + w * 0.67f, t + h * 0.27f);
            windows.lineTo(l + w * 0.79f, t + h * 0.41f);
            windows.close();
            p.setStyle(Paint.Style.FILL);
            p.setColor(Color.rgb(65, 78, 94));
            c.drawPath(windows, p);
            p.setStyle(Paint.Style.STROKE);
            p.setStrokeWidth(1f);
            p.setColor(Color.rgb(135, 145, 158));
            c.drawLine(l + w * 0.56f, t + h * 0.27f, l + w * 0.56f, t + h * 0.41f, p);

            p.setStyle(Paint.Style.FILL);
            p.setColor(Color.rgb(145, 154, 164));
            c.drawRoundRect(new RectF(l + w * 0.07f, t + h * 0.49f,
                    l + w * 0.21f, t + h * 0.64f), 3f, 3f, p);
            p.setColor(Color.rgb(226, 231, 236));
            c.drawRoundRect(new RectF(l + w * 0.82f, t + h * 0.47f,
                    l + w * 0.95f, t + h * 0.53f), 2f, 2f, p);
            p.setColor(Color.rgb(150, 157, 166));
            c.drawRect(l + w * 0.12f, t + h * 0.68f, l + w * 0.91f, t + h * 0.71f, p);
        }
        p.setStyle(Paint.Style.FILL);
    }

'''
s = s[:start] + new_vehicle_cards + s[end:]

# Recent parking cards: larger text and fully visible car illustration.
start = s.index('    private void drawRecentCard')
end = s.index('    private void editRecent', start)
new_recent = '''    private void drawRecentCard(Canvas c, int vehicle, float x, float y) {
        String location = prefs.getString("park_" + vehicle + "_location", "");
        String floor = prefs.getString("park_" + vehicle + "_floor", "");
        String time = prefs.getString("park_" + vehicle + "_time", "-");

        card(c, x, y, x + 346, y + 88, BORDER, Color.WHITE, 12, 1f);
        drawVehicleIllustration(c, vehicle, x + 12, y + 14, x + 108, y + 73);

        text(c, prefs.vehicleName(vehicle), x + 114, y + 29, 13.6f, TEXT, true);
        if (location.isEmpty()) {
            text(c, "저장된 위치 없음", x + 114, y + 52, 11f, MUTED, false);
            text(c, "-", x + 114, y + 72, 9.4f, MUTED, false);
        } else {
            text(c, (location.equals("집") ? "⌂ " : "▦ ") + location + " / " + floor,
                    x + 114, y + 52, 11f, BLUE, true);
            text(c, time, x + 114, y + 73, 9.4f, MUTED, false);
        }

        drawActionButton(c, x + 264, y + 22, x + 308, y + 66,
                "수정", BLUE, () -> editRecent(vehicle));
        drawActionButton(c, x + 313, y + 22, x + 344, y + 66,
                "삭제", RED, () -> deleteRecent(vehicle));
    }

    private void drawActionButton(Canvas c, float l, float t, float r, float b,
                                  String label, int color, Runnable action) {
        card(c, l, t, r, b, BORDER, Color.WHITE, 8, 1f);
        textCenterMiddle(c, label, (l + r) / 2f, (t + b) / 2f,
                10f, color, true);
        addHit(l, t, r, b, action);
    }

'''
s = s[:start] + new_recent + s[end:]

# Settings screen: increase fonts while preserving the single-screen layout.
start = s.index('    private void drawSettings(Canvas c) {')
end = s.index('    private void drawRegisteredVehicle', start)
new_settings = '''    private void drawSettings(Canvas c) {
        text(c, "‹", 22, 32, 32, TEXT, false);
        text(c, "자동감지 / 알림 설정", 55, 31, 20.5f, TEXT, true);
        addHit(10, 8, 48, 50, () -> screen = Screen.HOME);

        text(c, "자동 주차 감지", 22, 79, 13f, TEXT, true);
        card(c, 22, 92, 368, 160, BORDER, Color.WHITE, 12, 1f);
        bluetoothIcon(c, 48, 118);
        text(c, "차량 블루투스 연결 종료 감지", 72, 116, 12.8f, TEXT, true);
        text(c, "등록한 차량 연결이 끊기면 주차 상태를 감지합니다.",
                72, 137, 9.4f, MUTED, false);
        toggle(c, 323, 118, prefs.getBool("auto_detect", true));
        addHit(300, 96, 360, 153,
                () -> prefs.putBool("auto_detect", !prefs.getBool("auto_detect", true)));

        text(c, "등록된 차량", 22, 187, 13f, TEXT, true);
        drawRegisteredVehicle(c, 0, 22, 199);
        drawRegisteredVehicle(c, 1, 22, 269);

        text(c, "미저장 재알림", 22, 350, 13f, TEXT, true);
        card(c, 22, 363, 368, 536, BORDER, Color.WHITE, 12, 1f);
        bell(c, 49, 398, false);
        text(c, "주차 위치가 저장되지 않으면", 73, 395, 12.8f, TEXT, true);
        text(c, "알림을 다시 보내드립니다.", 73, 417, 10.5f, MUTED, false);
        toggle(c, 323, 398, prefs.getBool("reminder", true));
        addHit(300, 370, 360, 435,
                () -> prefs.putBool("reminder", !prefs.getBool("reminder", true)));

        text(c, "재알림 시간", 42, 470, 10.8f, MUTED, false);
        card(c, 142, 446, 348, 490, BORDER, BG, 8, 1f);
        text(c, "2분 후 알림", 158, 474, 12f, TEXT, true);
        text(c, "⌄", 327, 475, 14, MUTED, false);
        card(c, 42, 505, 348, 529, Color.TRANSPARENT, LIGHT_BLUE, 6, 0f);
        textCenterMiddle(c, "ⓘ  저장하지 않으면 2분 후 다시 알려줍니다.",
                195, 517, 9.2f, BLUE, false);

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
        drawVehicleIllustration(c, vehicle, x + 12, y + 8, x + 118, y + 53);
        textCenterMiddle(c, prefs.vehicleName(vehicle), x + 150, y + 30,
                13.5f, TEXT, true);

        String bluetoothName = prefs.getString("bt_name_" + vehicle, "");
        chip(c, x + 276, y + 16, x + 334, y + 44,
                bluetoothName.isEmpty() ? "등록" : "등록됨", BLUE, LIGHT_BLUE);
        addHit(x, y, x + 346, y + 60, () -> host.chooseBluetoothDevice(vehicle));
    }

'''
s = s[:start] + new_registered + s[end:]

# Engine-oil page: slightly larger text without changing the layout height.
s = s.replace('text(c, "차량 관리 / 엔진오일", 55, 31, 19, TEXT, true);',
              'text(c, "차량 관리 / 엔진오일", 55, 31, 20.5f, TEXT, true);')
s = s.replace('text(c, label, x + 54, y + 17, 11, MUTED, true);',
              'text(c, label, x + 54, y + 17, 12f, MUTED, true);')
s = s.replace('text(c, NumberFormat.getNumberInstance(Locale.KOREA).format(value), x + 72, y + 60, 18, TEXT, true);',
              'text(c, NumberFormat.getNumberInstance(Locale.KOREA).format(value), x + 72, y + 60, 19.5f, TEXT, true);')
s = s.replace('235, 449, 12, TEXT, true);', '235, 449, 13f, TEXT, true);')
s = s.replace('235, 480, 25, remain >= 0 ? BLUE : RED, true);',
              '235, 480, 27f, remain >= 0 ? BLUE : RED, true);')
s = s.replace('text(c, "정비 이력", 22, 675, 12, TEXT, true);',
              'text(c, "정비 이력", 22, 675, 13f, TEXT, true);')
s = s.replace('text(c, "전체 보기 ›", 306, 675, 10, BLUE, true);',
              'text(c, "전체 보기 ›", 302, 675, 10.8f, BLUE, true);')

# Shared controls: slightly larger labels throughout all three screens.
s = s.replace('textCenterMiddle(c, labels[i], a + w / 2, (t + b) / 2, 13,',
              'textCenterMiddle(c, labels[i], a + w / 2, (t + b) / 2, 14f,')
s = s.replace('textCenterMiddle(c, label, (l + r) / 2, (t + b) / 2, 13,',
              'textCenterMiddle(c, label, (l + r) / 2, (t + b) / 2, 14f,')
s = s.replace('float size = label.length() >= 5 ? 10.8f : 11.8f;',
              'float size = label.length() >= 5 ? 11.5f : 12.5f;')
s = s.replace('textCenter(c, label, (l + r) / 2, (t + b) / 2 + 4, 11,',
              'textCenter(c, label, (l + r) / 2, (t + b) / 2 + 4, 12.2f,')
s = s.replace('textCenter(c, label, (l + r) / 2, (t + b) / 2 + 4, 10, fg, true);',
              'textCenter(c, label, (l + r) / 2, (t + b) / 2 + 4, 10.8f, fg, true);')
s = s.replace('textCenter(c, labels[i], cx, 794, 10, color, i == selected);',
              'textCenter(c, labels[i], cx, 794, 11f, color, i == selected);')

view.write_text(s, encoding='utf-8')

from pathlib import Path
import re

root = Path('ParkingLocationPayload')

# Increase Android versionCode so Samsung Package Installer accepts this as an update.
gradle = root / 'app/build.gradle'
s = gradle.read_text(encoding='utf-8')
s = re.sub(r'versionCode\s+\d+', 'versionCode 6', s)
s = re.sub(r"versionName\s+'[^']+'", "versionName '1.0.6'", s)
s = re.sub(r'^\s*signingConfig signingConfigs\.debug\s*\n', '', s, flags=re.M)
gradle.write_text(s, encoding='utf-8')

view = root / 'app/src/main/java/com/interfaceworld/parkinglocation/ParkingView.java'
s = view.read_text(encoding='utf-8')

# Use the lower part of the screen more evenly while keeping every element above the nav bar.
s = s.replace('text(c, "최근 저장 위치", 22, 467, 12, TEXT, true);',
              'text(c, "최근 저장 위치", 22, 492, 12, TEXT, true);')
s = s.replace('drawRecentCard(c, 0, 22, 478);',
              'drawRecentCard(c, 0, 22, 504);')
s = s.replace('drawRecentCard(c, 1, 22, 546);',
              'drawRecentCard(c, 1, 22, 590);')

# Settings actions are lowered to balance the page, but remain clear of bottom navigation.
s = s.replace('button(c, 22, 542, 368, 588, "테스트 알림 보내기", false, host::testNotification);',
              'button(c, 22, 588, 368, 633, "테스트 알림 보내기", false, host::testNotification);')
s = s.replace('button(c, 22, 598, 368, 646, "설정 저장", true,',
              'button(c, 22, 645, 368, 693, "설정 저장", true,')

# Replace the whole bottom navigation method so its position is deterministic.
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
            textCenter(c, icons[i], cx, 771, 20, color, true);
            textCenter(c, labels[i], cx, 794, 10, color, i == selected);
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

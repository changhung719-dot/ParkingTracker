from pathlib import Path
import re
root = Path('ParkingLocationPayload')

# Version and unsigned release output
gradle = root / 'app/build.gradle'
s = gradle.read_text(encoding='utf-8')
s = re.sub(r'versionCode\s+\d+', 'versionCode 4', s)
s = re.sub(r"versionName\s+'[^']+'", "versionName '1.0.3'", s)
s = re.sub(r'^\s*signingConfig signingConfigs\.debug\s*\n', '', s, flags=re.M)
gradle.write_text(s, encoding='utf-8')

# Bluetooth receiver: passive exact-device matching only. It never connects,
# disconnects, requests audio focus, or controls media playback.
bt = root / 'app/src/main/java/com/interfaceworld/parkinglocation/BluetoothDisconnectReceiver.java'
bt.write_text(r'''package com.interfaceworld.parkinglocation;

import android.annotation.SuppressLint;
import android.bluetooth.BluetoothDevice;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

public class BluetoothDisconnectReceiver extends BroadcastReceiver {
    private static final long DUPLICATE_GUARD_MS = 5 * 60 * 1000L;

    @SuppressLint("MissingPermission")
    @Override public void onReceive(Context context, Intent intent) {
        String action = intent.getAction();
        if (!BluetoothDevice.ACTION_ACL_CONNECTED.equals(action)
                && !BluetoothDevice.ACTION_ACL_DISCONNECTED.equals(action)) return;

        Prefs prefs = new Prefs(context);
        BluetoothDevice device = intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE);
        if (device == null) return;

        final String address;
        try {
            address = device.getAddress();
        } catch (SecurityException ex) {
            return;
        }
        if (address == null || address.isEmpty()) return;

        int vehicle = -1;
        if (address.equalsIgnoreCase(prefs.getString("bt_0", ""))) vehicle = 0;
        else if (address.equalsIgnoreCase(prefs.getString("bt_1", ""))) vehicle = 1;
        if (vehicle < 0) return;

        if (BluetoothDevice.ACTION_ACL_CONNECTED.equals(action)) {
            prefs.putBool("bt_connected_" + vehicle, true);
            prefs.putLong("bt_connected_at_" + vehicle, System.currentTimeMillis());
            return;
        }

        prefs.putBool("bt_connected_" + vehicle, false);
        if (!prefs.getBool("auto_detect", true)) return;

        long now = System.currentTimeMillis();
        long last = prefs.getLong("bt_last_notice_" + vehicle, 0L);
        if (now - last < DUPLICATE_GUARD_MS) return;
        prefs.putLong("bt_last_notice_" + vehicle, now);

        prefs.putInt("selected_vehicle", vehicle);
        prefs.putBool("pending_save", true);
        NotificationHelper.showDetection(context, prefs.vehicleName(vehicle));
        NotificationHelper.scheduleReminder(context);
    }
}
''', encoding='utf-8')

# Preferences support for Bluetooth debounce times
prefs = root / 'app/src/main/java/com/interfaceworld/parkinglocation/Prefs.java'
s = prefs.read_text(encoding='utf-8')
if 'getLong(String key' not in s:
    s = s.replace(
        '    public String getString(String key, String def) { return sp.getString(key, def); }\n',
        '    public String getString(String key, String def) { return sp.getString(key, def); }\n'
        '    public long getLong(String key, long def) { return sp.getLong(key, def); }\n')
if 'putLong(String key' not in s:
    s = s.replace(
        '    public void putString(String key, String value) { sp.edit().putString(key, value).apply(); }\n',
        '    public void putString(String key, String value) { sp.edit().putString(key, value).apply(); }\n'
        '    public void putLong(String key, long value) { sp.edit().putLong(key, value).apply(); }\n')
prefs.write_text(s, encoding='utf-8')

# Manifest: receive connect/disconnect; no exact-alarm special permission required
manifest = root / 'app/src/main/AndroidManifest.xml'
s = manifest.read_text(encoding='utf-8')
s = s.replace('    <uses-permission android:name="android.permission.SCHEDULE_EXACT_ALARM" />\n', '')
if 'android.bluetooth.device.action.ACL_CONNECTED' not in s:
    s = s.replace(
        '                <action android:name="android.bluetooth.device.action.ACL_DISCONNECTED" />',
        '                <action android:name="android.bluetooth.device.action.ACL_CONNECTED" />\n'
        '                <action android:name="android.bluetooth.device.action.ACL_DISCONNECTED" />')
manifest.write_text(s, encoding='utf-8')

# Safe 2-minute reminder without exact-alarm permission screen
notif = root / 'app/src/main/java/com/interfaceworld/parkinglocation/NotificationHelper.java'
s = notif.read_text(encoding='utf-8')
start = s.index('        try {', s.index('public static void scheduleReminder'))
end = s.index('    }\n\n    public static void cancelReminder', start)
new_try = '''        try {
            if (Build.VERSION.SDK_INT >= 23) {
                am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, trigger, pi);
            } else {
                am.set(AlarmManager.RTC_WAKEUP, trigger, pi);
            }
        } catch (RuntimeException ex) {
            am.set(AlarmManager.RTC_WAKEUP, trigger, pi);
        }
'''
s = s[:start] + new_try + s[end:]
notif.write_text(s, encoding='utf-8')

# One-screen UI, correct car PNG rendering, and complete floor labels
view = root / 'app/src/main/java/com/interfaceworld/parkinglocation/ParkingView.java'
s = view.read_text(encoding='utf-8')
start = s.index('    private void drawHome(Canvas c) {')
end = s.index('    private void drawVehicleCards', start)
new_home = r'''    private void drawHome(Canvas c) {
        int location = prefs.getInt("selected_location", 0);
        boolean company = location == 1;

        text(c, "주차위치", 22, 30, 23, TEXT, true);
        chip(c, 22, 43, 128, 69, prefs.getBool("auto_detect", true) ? "● 자동 감지 ON" : "● 자동 감지 OFF", BLUE, LIGHT_BLUE);
        bell(c, 352, 28, true);

        text(c, "내 차량", 22, 92, 12, TEXT, true);
        drawVehicleCards(c, 22, 102, 86);

        text(c, "위치 유형", 22, 207, 12, TEXT, true);
        segment(c, 22, 217, 368, 257, new String[]{"⌂  집", "▦  회사"}, location, idx -> {
            prefs.putInt("selected_location", idx);
            int max = idx == 0 ? 5 : 2;
            if (prefs.getInt("selected_floor", 0) > max) prefs.putInt("selected_floor", max);
        });

        text(c, company ? "층 선택 (회사 주차장)" : "층 선택 (집 주차장)", 22, 282, 12, TEXT, true);
        float saveTop;
        if (company) {
            drawFloors(c, 1, 22, 294);
            card(c, 22, 340, 368, 378, Color.rgb(196, 218, 249), LIGHT_BLUE, 10, 1f);
            textCenterMiddle(c, "회사는 지하1층부터 지하3층까지만 선택할 수 있습니다.", 195, 359, 9.6f, BLUE, true);
            saveTop = 390;
        } else {
            drawFloors(c, 0, 22, 294);
            saveTop = 390;
        }

        button(c, 22, saveTop, 368, saveTop + 46, "현재 주차 위치 저장", true, this::saveParking);

        float recentTop = saveTop + 67;
        text(c, "최근 저장 위치", 22, recentTop, 12, TEXT, true);
        drawRecentCard(c, 0, 22, recentTop + 10);
        drawRecentCard(c, 1, 22, recentTop + 72);

        drawBottomNav(c, 1);
    }

'''
s = s[:start] + new_home + s[end:]
s = s.replace('scale = Math.min(sx, sy);', 'scale = Math.min(sx, sy); // 스크롤 없이 한 화면에 맞춤')
s = s.replace('drawBitmapFit(c, b, left + 18, y + 10, left + w - 18, y + 52);',
              'drawBitmapFit(c, b, left + 18, y + 8, left + w - 18, y + 50);')
s = s.replace('textCenter(c, prefs.vehicleName(i), left + w / 2, y + 79, 14, TEXT, true);',
              'textCenter(c, prefs.vehicleName(i), left + w / 2, y + 72, 13.5f, TEXT, true);')
s = s.replace('float t = y + row * 48;', 'float t = y + row * 43;')
s = s.replace('smallButton(c, l, t, l + w, t + 38, labels[i], on);',
              'smallButton(c, l, t, l + w, t + 36, labels[i], on);')
s = s.replace('addHit(l, t, l + w, t + 38, () -> prefs.putInt("selected_floor", idx));',
              'addHit(l, t, l + w, t + 36, () -> prefs.putInt("selected_floor", idx));')
# Complete button labels: no spaces, so all of 지하1층~지하5층 fits on one line
for n in range(1, 6):
    s = s.replace(f'"지하 {n}층"', f'"지하{n}층"')
# Saved display remains readable and edit matching ignores spaces
s = s.replace('String floor = prefs.getString("park_" + vehicle + "_floor", "지하1층");',
              'String floor = prefs.getString("park_" + vehicle + "_floor", "지하 1층");')
s = s.replace('if (f[i].equals(floor)) idx = i;',
              'if (f[i].replace(" ", "").equals(floor.replace(" ", ""))) idx = i;')
# Compact recent cards
s = s.replace('card(c, x, y, x + 346, y + 58, BORDER, Color.WHITE, 12, 1f);',
              'card(c, x, y, x + 346, y + 54, BORDER, Color.WHITE, 12, 1f);')
s = s.replace('x + 10, y + 11, x + 76, y + 46', 'x + 10, y + 9, x + 76, y + 45')
s = s.replace('x + 86, y + 23', 'x + 86, y + 21')
s = s.replace('x + 86, y + 43', 'x + 86, y + 40')
s = s.replace('x + 86, y + 42', 'x + 86, y + 39')
s = s.replace('x + 202, y + 44', 'x + 202, y + 41')
s = s.replace('x + 287, y + 36', 'x + 287, y + 33')
s = s.replace('x + 327, y + 36', 'x + 327, y + 33')
s = s.replace('x + 262, y + 8, x + 305, y + 50', 'x + 262, y + 6, x + 305, y + 48')
s = s.replace('x + 307, y + 8, x + 344, y + 50', 'x + 307, y + 6, x + 344, y + 48')
# Preserve real vehicle image aspect ratio
old_bitmap = '''    private void drawBitmapFit(Canvas c, Bitmap bitmap, float l, float t, float r, float b) {
        if (bitmap == null) return;
        RectF dst = new RectF(l, t, r, b);
        p.setAlpha(255);
        c.drawBitmap(bitmap, null, dst, p);
    }
'''
new_bitmap = '''    private void drawBitmapFit(Canvas c, Bitmap bitmap, float l, float t, float r, float b) {
        if (bitmap == null || bitmap.getWidth() <= 0 || bitmap.getHeight() <= 0) return;
        float boxW = r - l;
        float boxH = b - t;
        float imageRatio = bitmap.getWidth() / (float) bitmap.getHeight();
        float boxRatio = boxW / boxH;
        float drawW;
        float drawH;
        if (imageRatio > boxRatio) {
            drawW = boxW;
            drawH = boxW / imageRatio;
        } else {
            drawH = boxH;
            drawW = boxH * imageRatio;
        }
        float left = l + (boxW - drawW) / 2f;
        float top = t + (boxH - drawH) / 2f;
        RectF dst = new RectF(left, top, left + drawW, top + drawH);
        p.setAlpha(255);
        c.drawBitmap(bitmap, null, dst, p);
    }
'''
if old_bitmap not in s:
    raise RuntimeError('drawBitmapFit source block not found')
s = s.replace(old_bitmap, new_bitmap)
s = s.replace('Typeface.create("sans", Typeface.BOLD)', 'Typeface.create("sans-serif", Typeface.BOLD)')
s = s.replace('Typeface.create("sans", Typeface.NORMAL)', 'Typeface.create("sans-serif", Typeface.NORMAL)')
# Replace smallButton and add FontMetrics centered renderer
small_start = s.index('    private void smallButton(')
small_end = s.index('    private void chip(', small_start)
small = '''    private void smallButton(Canvas c, float l, float t, float r, float b, String label, boolean on) {
        card(c, l, t, r, b, on ? BLUE : BORDER, on ? BLUE : Color.WHITE, 8, 1f);
        float size = label.length() >= 5 ? 10.8f : 11.8f;
        textCenterMiddle(c, label, (l + r) / 2, (t + b) / 2, size, on ? Color.WHITE : TEXT, true);
    }

'''
s = s[:small_start] + small + s[small_end:]
insert_at = s.index('    private void circle(')
center_method = '''    private void textCenterMiddle(Canvas c, String textValue, float x, float centerY, float size, int color, boolean bold) {
        p.setStyle(Paint.Style.FILL);
        p.setColor(color);
        p.setTextSize(size);
        p.setTypeface(bold ? Typeface.create("sans-serif", Typeface.BOLD) : Typeface.create("sans-serif", Typeface.NORMAL));
        p.setTextAlign(Paint.Align.CENTER);
        Paint.FontMetrics fm = p.getFontMetrics();
        float baseline = centerY - (fm.ascent + fm.descent) / 2f;
        c.drawText(textValue, x, baseline, p);
        p.setTextAlign(Paint.Align.LEFT);
    }

'''
if 'private void textCenterMiddle' not in s:
    s = s[:insert_at] + center_method + s[insert_at:]
view.write_text(s, encoding='utf-8')

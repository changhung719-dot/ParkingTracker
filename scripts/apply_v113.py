from pathlib import Path
import re

root = Path('ParkingLocationPayload')
java = root / 'app/src/main/java/com/interfaceworld/parkinglocation'

# Version for direct update installation.
gradle = root / 'app/build.gradle'
s = gradle.read_text(encoding='utf-8')
s = re.sub(r'versionCode\s+\d+', 'versionCode 13', s)
s = re.sub(r"versionName\s+'[^']+'", "versionName '1.0.13'", s)
s = re.sub(r'^\s*signingConfig signingConfigs\.debug\s*\n', '', s, flags=re.M)
gradle.write_text(s, encoding='utf-8')

# Simple single-page UI matching the supplied legacy app screen.
(java / 'ParkingView.java').write_text(r'''package com.interfaceworld.parkinglocation;

import android.app.AlertDialog;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.view.MotionEvent;
import android.view.View;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;

public class ParkingView extends View {
    public interface Host {
        void showMessage(String text);
        void testNotification();
        void cancelParkingReminder();
        void editNumber(String key, String title, int currentValue);
        void chooseBluetoothDevice(int vehicle);
    }

    private static final float DW = 390f;
    private static final float DH = 780f;
    private static final int PURPLE = Color.rgb(75, 0, 196);
    private static final int TITLE = Color.rgb(111, 111, 111);
    private static final int DARK = Color.rgb(22, 22, 22);
    private static final int LINE = Color.rgb(215, 215, 215);
    private static final int BUTTON = Color.rgb(218, 220, 220);

    private final Host host;
    private final Prefs prefs;
    private final Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final List<Hit> hits = new ArrayList<>();
    private float scale = 1f;
    private float offsetX = 0f;
    private float offsetY = 0f;

    private static final class Hit {
        final RectF rect;
        final Runnable action;
        Hit(RectF rect, Runnable action) { this.rect = rect; this.action = action; }
    }

    public ParkingView(Context context, Host host, Prefs prefs) {
        super(context);
        this.host = host;
        this.prefs = prefs;
        setBackgroundColor(Color.WHITE);
        setLayerType(View.LAYER_TYPE_SOFTWARE, null);
    }

    public void openParking() {
        invalidate();
    }

    @Override protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        hits.clear();
        float sx = getWidth() / DW;
        float sy = getHeight() / DH;
        scale = Math.min(sx, sy);
        offsetX = (getWidth() - DW * scale) / 2f;
        offsetY = 0f;
        canvas.save();
        canvas.translate(offsetX, offsetY);
        canvas.scale(scale, scale);
        p.setStyle(Paint.Style.FILL);
        p.setColor(Color.WHITE);
        canvas.drawRect(0, 0, DW, DH, p);
        drawMain(canvas);
        canvas.restore();
    }

    @Override public boolean onTouchEvent(MotionEvent event) {
        if (event.getAction() != MotionEvent.ACTION_UP) return true;
        float x = (event.getX() - offsetX) / scale;
        float y = (event.getY() - offsetY) / scale;
        for (int i = hits.size() - 1; i >= 0; i--) {
            Hit hit = hits.get(i);
            if (hit.rect.contains(x, y)) {
                hit.action.run();
                invalidate();
                return true;
            }
        }
        return true;
    }

    private void drawMain(Canvas c) {
        String office = prefs.getString("office_seltos_floor", "B2");
        String homeSeltos = prefs.getString("home_seltos_floor", "B1");
        String homeG90 = prefs.getString("home_g90_floor", "B2");
        String lastSaved = prefs.getString("simple_last_saved", "저장 기록 없음");

        text(c, "주차 위치 저장", 24, 58, 34f, TITLE, true);
        addHit(18, 17, 260, 75, this::openBluetoothRegistration);

        text(c, "사무실 주차(셀토스)", 24, 120, 27f, TITLE, true);
        drawFloorRow(c, "셀토스 지하층:", office, 24, 166,
                () -> chooseFloor("사무실 셀토스 층 선택",
                        new String[]{"B1", "B2", "B3"}, office,
                        value -> prefs.putString("office_seltos_floor", value)));
        line(c, 24, 207, 366, 207);

        text(c, "집 주차장", 24, 257, 28f, TITLE, true);
        drawFloorRow(c, "셀토스 지하층:", homeSeltos, 24, 310,
                () -> chooseFloor("집 셀토스 층 선택",
                        new String[]{"1층", "B1", "B2", "B3", "B4", "B5"}, homeSeltos,
                        value -> prefs.putString("home_seltos_floor", value)));
        drawFloorRow(c, "G90 지하층:", homeG90, 24, 360,
                () -> chooseFloor("집 G90 층 선택",
                        new String[]{"1층", "B1", "B2", "B3", "B4", "B5"}, homeG90,
                        value -> prefs.putString("home_g90_floor", value)));

        p.setStyle(Paint.Style.FILL);
        p.setColor(BUTTON);
        p.setShadowLayer(3f, 0f, 2f, Color.argb(50, 0, 0, 0));
        c.drawRect(28, 398, 362, 447, p);
        p.clearShadowLayer();
        textCenter(c, "저장", 195, 432, 24f, DARK, true);
        addHit(28, 394, 362, 452, this::saveAll);

        text(c, "마지막 저장: " + lastSaved, 24, 493, 22f, TITLE, true);

        text(c, "차량 블루투스 등록은 제목을 누르세요.", 24, 740, 12f, Color.rgb(145,145,145), false);
    }

    private void drawFloorRow(Canvas c, String label, String value, float x, float baseline,
                              Runnable action) {
        text(c, label, x, baseline, 23f, TITLE, true);
        text(c, value, 176, baseline, 25f, DARK, true);
        triangle(c, 341, baseline - 10);
        addHit(20, baseline - 40, 370, baseline + 16, action);
    }

    private interface ValueConsumer { void accept(String value); }

    private void chooseFloor(String title, String[] options, String current, ValueConsumer consumer) {
        int checked = 0;
        for (int i = 0; i < options.length; i++) {
            if (options[i].equals(current)) checked = i;
        }
        final int selected = checked;
        new AlertDialog.Builder(getContext())
                .setTitle(title)
                .setSingleChoiceItems(options, selected, (dialog, which) -> {
                    consumer.accept(options[which]);
                    dialog.dismiss();
                    invalidate();
                })
                .setNegativeButton("취소", null)
                .show();
    }

    private void saveAll() {
        String now = new SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.KOREA).format(new Date());
        prefs.putString("simple_last_saved", now);
        prefs.putBool("pending_save", false);
        host.cancelParkingReminder();
        host.showMessage("주차 위치를 저장했습니다.");
        invalidate();
    }

    private void openBluetoothRegistration() {
        String[] items = {"셀토스 블루투스 등록", "G90 블루투스 등록"};
        new AlertDialog.Builder(getContext())
                .setTitle("차량 블루투스 등록")
                .setItems(items, (dialog, which) -> host.chooseBluetoothDevice(which))
                .setNegativeButton("취소", null)
                .show();
    }

    private void triangle(Canvas c, float x, float y) {
        p.setColor(Color.rgb(100, 100, 100));
        p.setStyle(Paint.Style.FILL);
        Path path = new Path();
        path.moveTo(x - 6, y);
        path.lineTo(x + 6, y);
        path.lineTo(x, y + 7);
        path.close();
        c.drawPath(path, p);
    }

    private void line(Canvas c, float x1, float y1, float x2, float y2) {
        p.setColor(LINE);
        p.setStrokeWidth(1f);
        c.drawLine(x1, y1, x2, y2, p);
    }

    private void text(Canvas c, String value, float x, float y, float size, int color, boolean bold) {
        p.setStyle(Paint.Style.FILL);
        p.setColor(color);
        p.setTextSize(size);
        p.setTypeface(Typeface.create("sans-serif", bold ? Typeface.BOLD : Typeface.NORMAL));
        p.setTextAlign(Paint.Align.LEFT);
        c.drawText(value, x, y, p);
    }

    private void textCenter(Canvas c, String value, float x, float y, float size, int color, boolean bold) {
        p.setStyle(Paint.Style.FILL);
        p.setColor(color);
        p.setTextSize(size);
        p.setTypeface(Typeface.create("sans-serif", bold ? Typeface.BOLD : Typeface.NORMAL));
        p.setTextAlign(Paint.Align.CENTER);
        c.drawText(value, x, y, p);
        p.setTextAlign(Paint.Align.LEFT);
    }

    private void addHit(float l, float t, float r, float b, Runnable action) {
        hits.add(new Hit(new RectF(l, t, r, b), action));
    }
}
''', encoding='utf-8')

(java / 'Prefs.java').write_text(r'''package com.interfaceworld.parkinglocation;

import android.content.Context;
import android.content.SharedPreferences;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

public final class Prefs {
    private static final String NAME = "parking_location_prefs";
    private final SharedPreferences sp;

    public Prefs(Context context) {
        sp = context.getSharedPreferences(NAME, Context.MODE_PRIVATE);
        initializeDefaults();
    }

    private void initializeDefaults() {
        SharedPreferences.Editor e = sp.edit();
        if (!sp.contains("auto_detect")) e.putBoolean("auto_detect", true);
        if (!sp.contains("reminder")) e.putBoolean("reminder", true);
        if (!sp.contains("selected_vehicle")) e.putInt("selected_vehicle", 0);
        if (!sp.contains("office_seltos_floor")) e.putString("office_seltos_floor", "B2");
        if (!sp.contains("home_seltos_floor")) e.putString("home_seltos_floor", "B1");
        if (!sp.contains("home_g90_floor")) e.putString("home_g90_floor", "B2");
        if (!sp.contains("simple_last_saved")) e.putString("simple_last_saved", "저장 기록 없음");
        e.apply();
    }

    public boolean getBool(String key, boolean def) { return sp.getBoolean(key, def); }
    public void putBool(String key, boolean value) { sp.edit().putBoolean(key, value).apply(); }
    public int getInt(String key, int def) { return sp.getInt(key, def); }
    public void putInt(String key, int value) { sp.edit().putInt(key, value).apply(); }
    public long getLong(String key, long def) { return sp.getLong(key, def); }
    public void putLong(String key, long value) { sp.edit().putLong(key, value).apply(); }
    public String getString(String key, String def) { return sp.getString(key, def); }
    public void putString(String key, String value) { sp.edit().putString(key, value).apply(); }
    public void remove(String key) { sp.edit().remove(key).apply(); }
    public String vehicleName(int index) { return index == 0 ? "셀토스" : "G90"; }

    public void saveParking(int vehicle, String location, String floor) {
        String now = new SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.KOREA).format(new Date());
        sp.edit()
                .putString("park_" + vehicle + "_location", location)
                .putString("park_" + vehicle + "_floor", floor)
                .putString("park_" + vehicle + "_time", now)
                .putBoolean("pending_save", false)
                .apply();
    }
}
''', encoding='utf-8')

(java / 'MainActivity.java').write_text(r'''package com.interfaceworld.parkinglocation;

import android.Manifest;
import android.annotation.SuppressLint;
import android.app.Activity;
import android.app.AlertDialog;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.text.InputType;
import android.view.View;
import android.view.Window;
import android.widget.EditText;
import android.widget.Toast;
import java.util.ArrayList;
import java.util.Set;

public class MainActivity extends Activity implements ParkingView.Host {
    private ParkingView parkingView;
    private Prefs prefs;

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Window window = getWindow();
        window.setStatusBarColor(Color.rgb(75, 0, 196));
        window.setNavigationBarColor(Color.WHITE);
        if (Build.VERSION.SDK_INT >= 26) {
            window.getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);
        } else {
            window.getDecorView().setSystemUiVisibility(0);
        }
        prefs = new Prefs(this);
        NotificationHelper.createChannels(this);
        parkingView = new ParkingView(this, this, prefs);
        setContentView(parkingView);
        requestRequiredPermissions();
        handleOpenIntent(getIntent());
        parkingView.postDelayed(this::maybeShowBluetoothSetup, 900L);
    }

    @Override protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        handleOpenIntent(intent);
    }

    @Override public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] results) {
        super.onRequestPermissionsResult(requestCode, permissions, results);
        parkingView.postDelayed(this::maybeShowBluetoothSetup, 350L);
    }

    private void handleOpenIntent(Intent intent) {
        if (intent != null && intent.hasExtra("open_source") && parkingView != null) {
            parkingView.openParking();
        }
    }

    private void requestRequiredPermissions() {
        ArrayList<String> permissions = new ArrayList<>();
        if (Build.VERSION.SDK_INT >= 33
                && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            permissions.add(Manifest.permission.POST_NOTIFICATIONS);
        }
        if (Build.VERSION.SDK_INT >= 31
                && checkSelfPermission(Manifest.permission.BLUETOOTH_CONNECT) != PackageManager.PERMISSION_GRANTED) {
            permissions.add(Manifest.permission.BLUETOOTH_CONNECT);
        }
        if (!permissions.isEmpty()) requestPermissions(permissions.toArray(new String[0]), 1001);
    }

    private void maybeShowBluetoothSetup() {
        if (isFinishing()) return;
        if (Build.VERSION.SDK_INT >= 31
                && checkSelfPermission(Manifest.permission.BLUETOOTH_CONNECT) != PackageManager.PERMISSION_GRANTED) return;
        if (prefs.getString("bt_0", "").isEmpty()) {
            showSetupDialog(0);
        } else if (prefs.getString("bt_1", "").isEmpty()) {
            showSetupDialog(1);
        }
    }

    private void showSetupDialog(int vehicle) {
        String car = prefs.vehicleName(vehicle);
        new AlertDialog.Builder(this)
                .setTitle(car + " 차량 블루투스 등록")
                .setMessage("차량 블루투스를 등록하면 연결이 끊어진 시간부터 3분 뒤 미저장 알림을 받을 수 있습니다.")
                .setNegativeButton("나중에", null)
                .setPositiveButton("등록하기", (dialog, which) -> chooseBluetoothDevice(vehicle))
                .show();
    }

    @Override public void showMessage(String text) {
        Toast.makeText(this, text, Toast.LENGTH_SHORT).show();
    }

    @Override public void testNotification() {
        prefs.putBool("pending_save", true);
        NotificationHelper.scheduleReminder(this);
        showMessage("저장하지 않으면 3분 후 알림을 보냅니다.");
    }

    @Override public void cancelParkingReminder() {
        prefs.putBool("pending_save", false);
        NotificationHelper.cancelReminder(this);
    }

    @Override public void editNumber(String key, String title, int currentValue) {
        EditText input = new EditText(this);
        input.setInputType(InputType.TYPE_CLASS_NUMBER);
        input.setText(String.valueOf(currentValue));
        new AlertDialog.Builder(this)
                .setTitle(title)
                .setView(input)
                .setNegativeButton("취소", null)
                .setPositiveButton("확인", (dialog, which) -> {
                    try {
                        prefs.putInt(key, Integer.parseInt(input.getText().toString().trim()));
                        parkingView.invalidate();
                    } catch (Exception ex) {
                        showMessage("숫자를 정확히 입력해 주세요.");
                    }
                }).show();
    }

    @SuppressLint("MissingPermission")
    @Override public void chooseBluetoothDevice(int vehicle) {
        if (Build.VERSION.SDK_INT >= 31
                && checkSelfPermission(Manifest.permission.BLUETOOTH_CONNECT) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.BLUETOOTH_CONNECT}, 1002);
            showMessage("권한을 허용한 뒤 다시 등록해 주세요.");
            return;
        }
        BluetoothAdapter adapter = BluetoothAdapter.getDefaultAdapter();
        if (adapter == null) {
            showMessage("이 휴대폰에서는 블루투스를 사용할 수 없습니다.");
            return;
        }
        if (!adapter.isEnabled()) {
            startActivity(new Intent(Settings.ACTION_BLUETOOTH_SETTINGS));
            showMessage("블루투스를 켜고 차량과 먼저 페어링해 주세요.");
            return;
        }
        Set<BluetoothDevice> devices = adapter.getBondedDevices();
        if (devices == null || devices.isEmpty()) {
            startActivity(new Intent(Settings.ACTION_BLUETOOTH_SETTINGS));
            showMessage("먼저 차량 블루투스를 휴대폰과 페어링해 주세요.");
            return;
        }
        ArrayList<BluetoothDevice> list = new ArrayList<>(devices);
        String[] names = new String[list.size()];
        for (int i = 0; i < list.size(); i++) {
            BluetoothDevice device = list.get(i);
            String name = device.getName() == null ? "이름 없는 장치" : device.getName();
            names[i] = name + "\n" + device.getAddress();
        }
        String car = prefs.vehicleName(vehicle);
        new AlertDialog.Builder(this)
                .setTitle(car + " 블루투스 장치 선택")
                .setItems(names, (dialog, which) -> {
                    BluetoothDevice device = list.get(which);
                    prefs.putString("bt_" + vehicle, device.getAddress());
                    prefs.putString("bt_name_" + vehicle,
                            device.getName() == null ? "등록된 장치" : device.getName());
                    showMessage(car + " 차량 블루투스가 등록되었습니다.");
                    if (vehicle == 0 && prefs.getString("bt_1", "").isEmpty()) {
                        parkingView.postDelayed(() -> showSetupDialog(1), 500L);
                    }
                })
                .setNegativeButton("취소", null)
                .show();
    }
}
''', encoding='utf-8')

(java / 'BluetoothDisconnectReceiver.java').write_text(r'''package com.interfaceworld.parkinglocation;

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

        String address;
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
            if (prefs.getBool("pending_save", false)
                    && prefs.getInt("selected_vehicle", -1) == vehicle) {
                prefs.putBool("pending_save", false);
                NotificationHelper.cancelReminder(context);
            }
            return;
        }

        prefs.putBool("bt_connected_" + vehicle, false);
        if (!prefs.getBool("auto_detect", true)) return;

        long now = System.currentTimeMillis();
        long last = prefs.getLong("bt_last_notice_" + vehicle, 0L);
        if (now - last < DUPLICATE_GUARD_MS) return;
        prefs.putLong("bt_last_notice_" + vehicle, now);
        prefs.putLong("bt_disconnected_at", now);
        prefs.putInt("selected_vehicle", vehicle);
        prefs.putBool("pending_save", true);
        NotificationHelper.scheduleReminder(context);
    }
}
''', encoding='utf-8')

(java / 'NotificationHelper.java').write_text(r'''package com.interfaceworld.parkinglocation;

import android.app.AlarmManager;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.os.Build;

public final class NotificationHelper {
    public static final String CHANNEL_DETECT = "parking_detect";
    public static final String CHANNEL_REMINDER = "parking_reminder_3min";
    public static final int ID_DETECT = 2101;
    public static final int ID_REMINDER = 2102;
    private static final int REQUEST_REMINDER = 9102;
    private static final long REMINDER_DELAY_MS = 3 * 60 * 1000L;

    private NotificationHelper() {}

    public static void createChannels(Context context) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationManager manager = context.getSystemService(NotificationManager.class);
            NotificationChannel reminder = new NotificationChannel(
                    CHANNEL_REMINDER, "주차 위치 미저장 알림", NotificationManager.IMPORTANCE_HIGH);
            reminder.setDescription("차량 블루투스 연결 종료 후 3분 뒤 주차 위치 저장을 안내합니다.");
            reminder.enableVibration(true);
            manager.createNotificationChannel(reminder);
        }
    }

    private static PendingIntent openAppIntent(Context context, String source) {
        Intent intent = new Intent(context, MainActivity.class);
        intent.putExtra("open_source", source);
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK
                | Intent.FLAG_ACTIVITY_CLEAR_TOP
                | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        return PendingIntent.getActivity(context, source.hashCode(), intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }

    public static void showDetection(Context context, String vehicle) {
        // Immediate notifications are intentionally suppressed. The requested alert is sent after 3 minutes.
    }

    public static void showReminder(Context context) {
        Prefs prefs = new Prefs(context);
        if (!prefs.getBool("pending_save", false) || !prefs.getBool("reminder", true)) return;
        String vehicle = prefs.vehicleName(prefs.getInt("selected_vehicle", 0));
        createChannels(context);
        Notification.Builder builder = Build.VERSION.SDK_INT >= 26
                ? new Notification.Builder(context, CHANNEL_REMINDER)
                : new Notification.Builder(context);
        String message = "주차 위치가 아직 저장되지 않았습니다.\n지금 층수를 선택하시겠습니까?";
        builder.setSmallIcon(android.R.drawable.ic_dialog_alert)
                .setContentTitle("주차 위치가 아직 저장되지 않았습니다.")
                .setContentText("지금 층수를 선택하시겠습니까?")
                .setStyle(new Notification.BigTextStyle().bigText(
                        vehicle + " 차량 블루투스 연결이 끊어진 후 3분이 지났습니다.\n" + message))
                .setContentIntent(openAppIntent(context, "reminder"))
                .setAutoCancel(true)
                .setPriority(Notification.PRIORITY_HIGH)
                .setCategory(Notification.CATEGORY_REMINDER)
                .addAction(new Notification.Action.Builder(
                        android.R.drawable.ic_menu_save,
                        "층수 선택",
                        openAppIntent(context, "reminder_action")).build());
        context.getSystemService(NotificationManager.class).notify(ID_REMINDER, builder.build());
    }

    public static void scheduleReminder(Context context) {
        Prefs prefs = new Prefs(context);
        if (!prefs.getBool("reminder", true)) return;
        Intent intent = new Intent(context, ReminderReceiver.class);
        PendingIntent pendingIntent = PendingIntent.getBroadcast(context, REQUEST_REMINDER, intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        AlarmManager alarmManager = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        long trigger = System.currentTimeMillis() + REMINDER_DELAY_MS;
        try {
            if (Build.VERSION.SDK_INT >= 23) {
                alarmManager.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, trigger, pendingIntent);
            } else {
                alarmManager.set(AlarmManager.RTC_WAKEUP, trigger, pendingIntent);
            }
        } catch (RuntimeException ex) {
            alarmManager.set(AlarmManager.RTC_WAKEUP, trigger, pendingIntent);
        }
    }

    public static void cancelReminder(Context context) {
        Intent intent = new Intent(context, ReminderReceiver.class);
        PendingIntent pendingIntent = PendingIntent.getBroadcast(context, REQUEST_REMINDER, intent,
                PendingIntent.FLAG_NO_CREATE | PendingIntent.FLAG_IMMUTABLE);
        if (pendingIntent != null) {
            ((AlarmManager) context.getSystemService(Context.ALARM_SERVICE)).cancel(pendingIntent);
            pendingIntent.cancel();
        }
        NotificationManager manager = context.getSystemService(NotificationManager.class);
        manager.cancel(ID_DETECT);
        manager.cancel(ID_REMINDER);
    }
}
''', encoding='utf-8')

manifest = root / 'app/src/main/AndroidManifest.xml'
s = manifest.read_text(encoding='utf-8')
s = s.replace('android:label="주차위치"', 'android:label="주차 위치 저장"')
manifest.write_text(s, encoding='utf-8')

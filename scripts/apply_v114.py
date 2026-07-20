from pathlib import Path
import re

root = Path('ParkingLocationPayload')
java = root / 'app/src/main/java/com/interfaceworld/parkinglocation'

# Version update
gradle = root / 'app/build.gradle'
s = gradle.read_text(encoding='utf-8')
s = re.sub(r'versionCode\s+\d+', 'versionCode 14', s)
s = re.sub(r"versionName\s+'[^']+'", "versionName '1.0.14'", s)
s = re.sub(r'^\s*signingConfig signingConfigs\.debug\s*\n', '', s, flags=re.M)
gradle.write_text(s, encoding='utf-8')

# Simple UI: same legacy screen plus a visible Bluetooth ON/OFF switch.
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
        void setBluetoothMonitoringEnabled(boolean enabled);
    }

    private static final float DW = 390f;
    private static final float DH = 780f;
    private static final int PURPLE = Color.rgb(75, 0, 196);
    private static final int TITLE = Color.rgb(105, 105, 105);
    private static final int DARK = Color.rgb(22, 22, 22);
    private static final int LINE = Color.rgb(215, 215, 215);
    private static final int BUTTON = Color.rgb(218, 220, 220);
    private static final int BLUE = Color.rgb(35, 113, 230);

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

    public void openParking() { invalidate(); }

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
        boolean monitorOn = prefs.getBool("auto_detect", true);

        text(c, "주차 위치 저장", 24, 55, 33f, TITLE, true);
        addHit(18, 14, 260, 70, this::openBluetoothRegistration);

        text(c, "블루투스 주차 알림", 24, 92, 18f, TITLE, true);
        text(c, monitorOn ? "ON" : "OFF", 268, 92, 17f, monitorOn ? BLUE : TITLE, true);
        drawSwitch(c, 334, 83, monitorOn);
        addHit(250, 64, 374, 109, () -> {
            boolean enabled = !prefs.getBool("auto_detect", true);
            prefs.putBool("auto_detect", enabled);
            host.setBluetoothMonitoringEnabled(enabled);
        });
        text(c, "차량 연결 종료 후 3분 뒤 미저장 알림", 24, 113, 12.5f, Color.rgb(135,135,135), false);

        text(c, "사무실 주차(셀토스)", 24, 158, 25f, TITLE, true);
        drawFloorRow(c, "셀토스 지하층:", office, 24, 201,
                () -> chooseFloor("사무실 셀토스 층 선택",
                        new String[]{"B1", "B2", "B3"}, office,
                        value -> prefs.putString("office_seltos_floor", value)));
        line(c, 24, 232, 366, 232);

        text(c, "집 주차장", 24, 276, 27f, TITLE, true);
        drawFloorRow(c, "셀토스 지하층:", homeSeltos, 24, 324,
                () -> chooseFloor("집 셀토스 층 선택",
                        new String[]{"1층", "B1", "B2", "B3", "B4", "B5"}, homeSeltos,
                        value -> prefs.putString("home_seltos_floor", value)));
        drawFloorRow(c, "G90 지하층:", homeG90, 24, 372,
                () -> chooseFloor("집 G90 층 선택",
                        new String[]{"1층", "B1", "B2", "B3", "B4", "B5"}, homeG90,
                        value -> prefs.putString("home_g90_floor", value)));

        p.setStyle(Paint.Style.FILL);
        p.setColor(BUTTON);
        p.setShadowLayer(3f, 0f, 2f, Color.argb(50, 0, 0, 0));
        c.drawRect(28, 407, 362, 458, p);
        p.clearShadowLayer();
        textCenter(c, "저장", 195, 442, 24f, DARK, true);
        addHit(28, 403, 362, 463, this::saveAll);

        text(c, "마지막 저장: " + lastSaved, 24, 505, 21f, TITLE, true);
        text(c, "차량 블루투스 등록은 제목을 누르세요.", 24, 742, 12f, Color.rgb(145,145,145), false);
    }

    private void drawSwitch(Canvas c, float cx, float cy, boolean on) {
        p.setStyle(Paint.Style.FILL);
        p.setColor(on ? BLUE : Color.rgb(190, 196, 205));
        RectF track = new RectF(cx - 23, cy - 11, cx + 23, cy + 11);
        c.drawRoundRect(track, 11, 11, p);
        p.setColor(Color.WHITE);
        float knobX = on ? cx + 11 : cx - 11;
        c.drawCircle(knobX, cy, 9, p);
    }

    private void drawFloorRow(Canvas c, String label, String value, float x, float baseline,
                              Runnable action) {
        text(c, label, x, baseline, 22f, TITLE, true);
        text(c, value, 176, baseline, 24f, DARK, true);
        triangle(c, 341, baseline - 10);
        addHit(20, baseline - 40, 370, baseline + 16, action);
    }

    private interface ValueConsumer { void accept(String value); }

    private void chooseFloor(String title, String[] options, String current, ValueConsumer consumer) {
        int checked = 0;
        for (int i = 0; i < options.length; i++) if (options[i].equals(current)) checked = i;
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
        }
        prefs = new Prefs(this);
        NotificationHelper.createChannels(this);
        parkingView = new ParkingView(this, this, prefs);
        setContentView(parkingView);
        requestRequiredPermissions();
        handleOpenIntent(getIntent());
        parkingView.postDelayed(this::syncMonitorState, 1000L);
        parkingView.postDelayed(this::maybeShowBluetoothSetup, 1300L);
    }

    @Override protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        handleOpenIntent(intent);
    }

    @Override public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] results) {
        super.onRequestPermissionsResult(requestCode, permissions, results);
        parkingView.postDelayed(this::syncMonitorState, 300L);
        parkingView.postDelayed(this::maybeShowBluetoothSetup, 600L);
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

    private boolean permissionsReady() {
        if (Build.VERSION.SDK_INT >= 31
                && checkSelfPermission(Manifest.permission.BLUETOOTH_CONNECT) != PackageManager.PERMISSION_GRANTED) {
            return false;
        }
        if (Build.VERSION.SDK_INT >= 33
                && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            return false;
        }
        return true;
    }

    private void syncMonitorState() {
        if (prefs.getBool("auto_detect", true)) {
            if (!permissionsReady()) {
                requestRequiredPermissions();
                return;
            }
            BluetoothMonitorService.start(this);
        } else {
            BluetoothMonitorService.stop(this);
        }
        if (parkingView != null) parkingView.invalidate();
    }

    private void maybeShowBluetoothSetup() {
        if (isFinishing() || !prefs.getBool("auto_detect", true) || !permissionsReady()) return;
        if (prefs.getString("bt_0", "").isEmpty()) showSetupDialog(0);
        else if (prefs.getString("bt_1", "").isEmpty()) showSetupDialog(1);
    }

    private void showSetupDialog(int vehicle) {
        String car = prefs.vehicleName(vehicle);
        new AlertDialog.Builder(this)
                .setTitle(car + " 차량 블루투스 등록")
                .setMessage("차량 블루투스를 등록하면 시동 종료 후 연결이 끊긴 시점부터 3분 뒤 알림을 받을 수 있습니다.")
                .setNegativeButton("나중에", null)
                .setPositiveButton("등록하기", (dialog, which) -> chooseBluetoothDevice(vehicle))
                .show();
    }

    @Override public void setBluetoothMonitoringEnabled(boolean enabled) {
        prefs.putBool("auto_detect", enabled);
        if (enabled) {
            if (!permissionsReady()) {
                requestRequiredPermissions();
                showMessage("알림과 블루투스 권한을 허용해 주세요.");
            } else {
                BluetoothMonitorService.start(this);
                maybeShowBluetoothSetup();
                showMessage("블루투스 주차 알림을 켰습니다.");
            }
        } else {
            prefs.putBool("pending_save", false);
            NotificationHelper.cancelReminder(this);
            BluetoothMonitorService.stop(this);
            showMessage("블루투스 주차 알림을 껐습니다.");
        }
        parkingView.invalidate();
    }

    @Override public void showMessage(String text) {
        Toast.makeText(this, text, Toast.LENGTH_SHORT).show();
    }

    @Override public void testNotification() {
        prefs.putBool("pending_save", true);
        prefs.putLong("reminder_due_at", System.currentTimeMillis() + 3 * 60 * 1000L);
        NotificationHelper.scheduleReminder(this);
        BluetoothMonitorService.refreshPendingTimer(this);
        showMessage("저장하지 않으면 3분 후 알림을 보냅니다.");
    }

    @Override public void cancelParkingReminder() {
        prefs.putBool("pending_save", false);
        prefs.putLong("reminder_due_at", 0L);
        NotificationHelper.cancelReminder(this);
        BluetoothMonitorService.cancelPending(this);
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
                    prefs.putBool("auto_detect", true);
                    BluetoothMonitorService.start(this);
                    showMessage(car + " 차량 블루투스가 등록되었습니다.");
                    if (vehicle == 0 && prefs.getString("bt_1", "").isEmpty()) {
                        parkingView.postDelayed(() -> showSetupDialog(1), 500L);
                    }
                    parkingView.invalidate();
                })
                .setNegativeButton("취소", null)
                .show();
    }
}
''', encoding='utf-8')

# Reliable foreground monitor: dynamically receives ACL and profile state broadcasts.
(java / 'BluetoothMonitorService.java').write_text(r'''package com.interfaceworld.parkinglocation;

import android.annotation.SuppressLint;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.bluetooth.BluetoothA2dp;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothHeadset;
import android.bluetooth.BluetoothProfile;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import java.util.HashMap;
import java.util.Map;

public class BluetoothMonitorService extends Service {
    private static final String CHANNEL = "parking_bt_monitor";
    private static final int NOTIFICATION_ID = 2201;
    private static final String ACTION_CANCEL = "com.interfaceworld.parkinglocation.CANCEL_PENDING";
    private static final String ACTION_REFRESH = "com.interfaceworld.parkinglocation.REFRESH_PENDING";
    private static final long REMINDER_DELAY = 3 * 60 * 1000L;
    private static final long PROFILE_VERIFY_DELAY = 12 * 1000L;
    private static final long DUPLICATE_GUARD = 30 * 1000L;

    private final Handler handler = new Handler(Looper.getMainLooper());
    private final Map<Integer, Runnable> verifyTasks = new HashMap<>();
    private Runnable reminderTask;
    private Prefs prefs;
    private boolean registered;

    public static void start(Context context) {
        Intent intent = new Intent(context, BluetoothMonitorService.class);
        if (Build.VERSION.SDK_INT >= 26) context.startForegroundService(intent);
        else context.startService(intent);
    }

    public static void stop(Context context) {
        context.stopService(new Intent(context, BluetoothMonitorService.class));
    }

    public static void cancelPending(Context context) {
        Intent intent = new Intent(context, BluetoothMonitorService.class).setAction(ACTION_CANCEL);
        if (Build.VERSION.SDK_INT >= 26) context.startForegroundService(intent);
        else context.startService(intent);
    }

    public static void refreshPendingTimer(Context context) {
        Intent intent = new Intent(context, BluetoothMonitorService.class).setAction(ACTION_REFRESH);
        if (Build.VERSION.SDK_INT >= 26) context.startForegroundService(intent);
        else context.startService(intent);
    }

    @Override public void onCreate() {
        super.onCreate();
        prefs = new Prefs(this);
        createChannel();
        startForeground(NOTIFICATION_ID, buildMonitorNotification());
        registerBluetoothReceiver();
        restorePendingTimer();
    }

    @Override public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null && ACTION_CANCEL.equals(intent.getAction())) {
            cancelPendingInternal();
        } else if (intent != null && ACTION_REFRESH.equals(intent.getAction())) {
            restorePendingTimer();
        }
        if (!prefs.getBool("auto_detect", true)) {
            stopSelf();
            return START_NOT_STICKY;
        }
        NotificationManager nm = getSystemService(NotificationManager.class);
        nm.notify(NOTIFICATION_ID, buildMonitorNotification());
        return START_STICKY;
    }

    private void createChannel() {
        if (Build.VERSION.SDK_INT >= 26) {
            NotificationChannel channel = new NotificationChannel(
                    CHANNEL, "블루투스 주차 감지", NotificationManager.IMPORTANCE_LOW);
            channel.setDescription("등록 차량의 블루투스 연결 종료를 감지합니다.");
            channel.setSound(null, null);
            channel.enableVibration(false);
            getSystemService(NotificationManager.class).createNotificationChannel(channel);
        }
    }

    private Notification buildMonitorNotification() {
        Intent open = new Intent(this, MainActivity.class)
                .setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        PendingIntent pi = PendingIntent.getActivity(this, 2201, open,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        Notification.Builder builder = Build.VERSION.SDK_INT >= 26
                ? new Notification.Builder(this, CHANNEL)
                : new Notification.Builder(this);
        return builder.setSmallIcon(android.R.drawable.stat_sys_data_bluetooth)
                .setContentTitle("블루투스 주차 알림 ON")
                .setContentText("셀토스·G90 연결 종료를 감지하고 있습니다.")
                .setContentIntent(pi)
                .setOngoing(true)
                .setCategory(Notification.CATEGORY_SERVICE)
                .setPriority(Notification.PRIORITY_LOW)
                .build();
    }

    private void registerBluetoothReceiver() {
        if (registered) return;
        IntentFilter filter = new IntentFilter();
        filter.addAction(BluetoothDevice.ACTION_ACL_CONNECTED);
        filter.addAction(BluetoothDevice.ACTION_ACL_DISCONNECTED);
        filter.addAction(BluetoothDevice.ACTION_ACL_DISCONNECT_REQUESTED);
        filter.addAction(BluetoothA2dp.ACTION_CONNECTION_STATE_CHANGED);
        filter.addAction(BluetoothHeadset.ACTION_CONNECTION_STATE_CHANGED);
        if (Build.VERSION.SDK_INT >= 33) registerReceiver(receiver, filter, Context.RECEIVER_EXPORTED);
        else registerReceiver(receiver, filter);
        registered = true;
    }

    private final BroadcastReceiver receiver = new BroadcastReceiver() {
        @SuppressLint("MissingPermission")
        @Override public void onReceive(Context context, Intent intent) {
            BluetoothDevice device = intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE);
            if (device == null) return;
            String address;
            try { address = device.getAddress(); }
            catch (SecurityException ex) { return; }
            int vehicle = vehicleForAddress(address);
            if (vehicle < 0) return;

            String action = intent.getAction();
            if (BluetoothDevice.ACTION_ACL_CONNECTED.equals(action)) {
                prefs.putBool("acl_connected_" + vehicle, true);
                cancelVehiclePending(vehicle);
                return;
            }
            if (BluetoothDevice.ACTION_ACL_DISCONNECTED.equals(action)
                    || BluetoothDevice.ACTION_ACL_DISCONNECT_REQUESTED.equals(action)) {
                prefs.putBool("acl_connected_" + vehicle, false);
                scheduleDisconnectVerification(vehicle, 1500L, true);
                return;
            }

            int state = intent.getIntExtra(BluetoothProfile.EXTRA_STATE, BluetoothProfile.STATE_DISCONNECTED);
            if (BluetoothA2dp.ACTION_CONNECTION_STATE_CHANGED.equals(action)) {
                if (state == BluetoothProfile.STATE_CONNECTED) {
                    prefs.putBool("a2dp_seen_" + vehicle, true);
                    prefs.putBool("a2dp_connected_" + vehicle, true);
                    cancelVehiclePending(vehicle);
                } else if (state == BluetoothProfile.STATE_DISCONNECTED) {
                    prefs.putBool("a2dp_connected_" + vehicle, false);
                    scheduleDisconnectVerification(vehicle, PROFILE_VERIFY_DELAY, false);
                }
            } else if (BluetoothHeadset.ACTION_CONNECTION_STATE_CHANGED.equals(action)) {
                if (state == BluetoothProfile.STATE_CONNECTED) {
                    prefs.putBool("headset_seen_" + vehicle, true);
                    prefs.putBool("headset_connected_" + vehicle, true);
                    cancelVehiclePending(vehicle);
                } else if (state == BluetoothProfile.STATE_DISCONNECTED) {
                    prefs.putBool("headset_connected_" + vehicle, false);
                    scheduleDisconnectVerification(vehicle, PROFILE_VERIFY_DELAY, false);
                }
            }
        }
    };

    private int vehicleForAddress(String address) {
        if (address == null) return -1;
        if (address.equalsIgnoreCase(prefs.getString("bt_0", ""))) return 0;
        if (address.equalsIgnoreCase(prefs.getString("bt_1", ""))) return 1;
        return -1;
    }

    private void scheduleDisconnectVerification(int vehicle, long delay, boolean aclEvent) {
        Runnable old = verifyTasks.remove(vehicle);
        if (old != null) handler.removeCallbacks(old);
        Runnable task = () -> {
            verifyTasks.remove(vehicle);
            if (!prefs.getBool("auto_detect", true)) return;
            boolean aclConnected = prefs.getBool("acl_connected_" + vehicle, false);
            boolean a2dpConnected = prefs.getBool("a2dp_connected_" + vehicle, false);
            boolean headsetConnected = prefs.getBool("headset_connected_" + vehicle, false);
            boolean a2dpSeen = prefs.getBool("a2dp_seen_" + vehicle, false);
            boolean headsetSeen = prefs.getBool("headset_seen_" + vehicle, false);
            boolean profilesDisconnected = (!a2dpSeen || !a2dpConnected)
                    && (!headsetSeen || !headsetConnected)
                    && (a2dpSeen || headsetSeen);
            if ((aclEvent && !aclConnected) || profilesDisconnected) triggerPending(vehicle);
        };
        verifyTasks.put(vehicle, task);
        handler.postDelayed(task, delay);
    }

    private void triggerPending(int vehicle) {
        long now = System.currentTimeMillis();
        long last = prefs.getLong("bt_last_notice_" + vehicle, 0L);
        if (now - last < DUPLICATE_GUARD) return;
        prefs.putLong("bt_last_notice_" + vehicle, now);
        prefs.putLong("bt_disconnected_at", now);
        prefs.putLong("reminder_due_at", now + REMINDER_DELAY);
        prefs.putInt("selected_vehicle", vehicle);
        prefs.putBool("pending_save", true);
        scheduleHandlerReminder(REMINDER_DELAY);
        NotificationHelper.scheduleReminder(this);
    }

    private void scheduleHandlerReminder(long delay) {
        if (reminderTask != null) handler.removeCallbacks(reminderTask);
        reminderTask = () -> {
            if (prefs.getBool("pending_save", false) && prefs.getBool("auto_detect", true)) {
                NotificationHelper.showReminder(this);
            }
        };
        handler.postDelayed(reminderTask, Math.max(0L, delay));
    }

    private void restorePendingTimer() {
        if (!prefs.getBool("pending_save", false)) return;
        long due = prefs.getLong("reminder_due_at", 0L);
        if (due <= 0L) return;
        scheduleHandlerReminder(due - System.currentTimeMillis());
    }

    private void cancelVehiclePending(int vehicle) {
        Runnable verify = verifyTasks.remove(vehicle);
        if (verify != null) handler.removeCallbacks(verify);
        if (prefs.getBool("pending_save", false)
                && prefs.getInt("selected_vehicle", -1) == vehicle) {
            cancelPendingInternal();
        }
    }

    private void cancelPendingInternal() {
        if (reminderTask != null) handler.removeCallbacks(reminderTask);
        reminderTask = null;
        prefs.putBool("pending_save", false);
        prefs.putLong("reminder_due_at", 0L);
        NotificationHelper.cancelReminder(this);
    }

    @Override public void onDestroy() {
        if (registered) {
            try { unregisterReceiver(receiver); } catch (Exception ignored) {}
            registered = false;
        }
        for (Runnable task : verifyTasks.values()) handler.removeCallbacks(task);
        verifyTasks.clear();
        if (reminderTask != null) handler.removeCallbacks(reminderTask);
        super.onDestroy();
    }

    @Override public IBinder onBind(Intent intent) { return null; }
}
''', encoding='utf-8')

(java / 'BootReceiver.java').write_text(r'''package com.interfaceworld.parkinglocation;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

public class BootReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context context, Intent intent) {
        Prefs prefs = new Prefs(context);
        if (prefs.getBool("auto_detect", true)) {
            try { BluetoothMonitorService.start(context); } catch (RuntimeException ignored) {}
        }
    }
}
''', encoding='utf-8')

# Keep the manifest receiver as a lightweight backup that forwards into the running monitor.
(java / 'BluetoothDisconnectReceiver.java').write_text(r'''package com.interfaceworld.parkinglocation;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

public class BluetoothDisconnectReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context context, Intent intent) {
        Prefs prefs = new Prefs(context);
        if (!prefs.getBool("auto_detect", true)) return;
        try { BluetoothMonitorService.start(context); } catch (RuntimeException ignored) {}
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
import android.os.SystemClock;

public final class NotificationHelper {
    public static final String CHANNEL_REMINDER = "parking_reminder_3min_v2";
    public static final int ID_REMINDER = 2102;
    private static final int REQUEST_REMINDER = 9102;
    private static final long REMINDER_DELAY_MS = 3 * 60 * 1000L;

    private NotificationHelper() {}

    public static void createChannels(Context context) {
        if (Build.VERSION.SDK_INT >= 26) {
            NotificationChannel reminder = new NotificationChannel(
                    CHANNEL_REMINDER, "주차 위치 미저장 알림", NotificationManager.IMPORTANCE_HIGH);
            reminder.setDescription("차량 블루투스 연결 종료 후 3분 뒤 주차 위치 저장을 안내합니다.");
            reminder.enableVibration(true);
            context.getSystemService(NotificationManager.class).createNotificationChannel(reminder);
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

    public static void showDetection(Context context, String vehicle) { }

    public static void showReminder(Context context) {
        Prefs prefs = new Prefs(context);
        if (!prefs.getBool("pending_save", false)
                || !prefs.getBool("reminder", true)
                || !prefs.getBool("auto_detect", true)) return;
        String vehicle = prefs.vehicleName(prefs.getInt("selected_vehicle", 0));
        createChannels(context);
        Notification.Builder builder = Build.VERSION.SDK_INT >= 26
                ? new Notification.Builder(context, CHANNEL_REMINDER)
                : new Notification.Builder(context);
        builder.setSmallIcon(android.R.drawable.ic_dialog_alert)
                .setContentTitle("주차 위치가 아직 저장되지 않았습니다.")
                .setContentText("지금 층수를 선택하시겠습니까?")
                .setStyle(new Notification.BigTextStyle().bigText(
                        vehicle + " 차량 블루투스 연결이 끊어진 후 3분이 지났습니다.\n"
                                + "주차 위치가 아직 저장되지 않았습니다.\n"
                                + "지금 층수를 선택하시겠습니까?"))
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
        if (!prefs.getBool("reminder", true) || !prefs.getBool("auto_detect", true)) return;
        Intent intent = new Intent(context, ReminderReceiver.class);
        PendingIntent pi = PendingIntent.getBroadcast(context, REQUEST_REMINDER, intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        AlarmManager am = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        long trigger = SystemClock.elapsedRealtime() + REMINDER_DELAY_MS;
        try {
            if (Build.VERSION.SDK_INT >= 23) {
                am.setAndAllowWhileIdle(AlarmManager.ELAPSED_REALTIME_WAKEUP, trigger, pi);
            } else {
                am.set(AlarmManager.ELAPSED_REALTIME_WAKEUP, trigger, pi);
            }
        } catch (RuntimeException ex) {
            am.set(AlarmManager.ELAPSED_REALTIME_WAKEUP, trigger, pi);
        }
    }

    public static void cancelReminder(Context context) {
        Intent intent = new Intent(context, ReminderReceiver.class);
        PendingIntent pi = PendingIntent.getBroadcast(context, REQUEST_REMINDER, intent,
                PendingIntent.FLAG_NO_CREATE | PendingIntent.FLAG_IMMUTABLE);
        if (pi != null) {
            ((AlarmManager) context.getSystemService(Context.ALARM_SERVICE)).cancel(pi);
            pi.cancel();
        }
        context.getSystemService(NotificationManager.class).cancel(ID_REMINDER);
    }
}
''', encoding='utf-8')

# Manifest permissions and service declarations.
manifest = root / 'app/src/main/AndroidManifest.xml'
s = manifest.read_text(encoding='utf-8')
if 'android.permission.FOREGROUND_SERVICE"' not in s:
    s = s.replace('<uses-permission android:name="android.permission.BLUETOOTH_CONNECT" />',
                  '<uses-permission android:name="android.permission.BLUETOOTH_CONNECT" />\n'
                  '    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />\n'
                  '    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_CONNECTED_DEVICE" />\n'
                  '    <uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />')
if '.BluetoothMonitorService' not in s:
    s = s.replace('        <receiver\n            android:name=".BluetoothDisconnectReceiver"',
                  '        <service\n'
                  '            android:name=".BluetoothMonitorService"\n'
                  '            android:exported="false"\n'
                  '            android:stopWithTask="false"\n'
                  '            android:foregroundServiceType="connectedDevice" />\n\n'
                  '        <receiver\n            android:name=".BluetoothDisconnectReceiver"')
if '.BootReceiver' not in s:
    s = s.replace('        <receiver\n            android:name=".ReminderReceiver"',
                  '        <receiver\n'
                  '            android:name=".BootReceiver"\n'
                  '            android:enabled="true"\n'
                  '            android:exported="true">\n'
                  '            <intent-filter>\n'
                  '                <action android:name="android.intent.action.BOOT_COMPLETED" />\n'
                  '                <action android:name="android.intent.action.MY_PACKAGE_REPLACED" />\n'
                  '            </intent-filter>\n'
                  '        </receiver>\n\n'
                  '        <receiver\n            android:name=".ReminderReceiver"')
s = s.replace('android:label="주차위치"', 'android:label="주차 위치 저장"')
manifest.write_text(s, encoding='utf-8')

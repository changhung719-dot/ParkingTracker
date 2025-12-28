package com.example.parkingtracker

import android.os.Bundle
import android.widget.ArrayAdapter
import android.widget.Button
import android.widget.Spinner
import android.widget.TextView
import androidx.activity.ComponentActivity
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.intPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

private val ComponentActivity.dataStore by preferencesDataStore(name = "parking_prefs")

class MainActivity : ComponentActivity() {

    private val KEY_OFFICE_SELTOS = intPreferencesKey("office_seltos_index")
    private val KEY_HOME_SELTOS = intPreferencesKey("home_seltos_index")
    private val KEY_HOME_G90 = intPreferencesKey("home_g90_index")
    private val KEY_LAST_SAVED = stringPreferencesKey("last_saved")

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        val spOfficeSeltos = findViewById<Spinner>(R.id.spOfficeSeltos)
        val spHomeSeltos = findViewById<Spinner>(R.id.spHomeSeltos)
        val spHomeG90 = findViewById<Spinner>(R.id.spHomeG90)
        val btnSave = findViewById<Button>(R.id.btnSave)
        val tvLastSaved = findViewById<TextView>(R.id.tvLastSaved)

        val officeFloors = listOf("B1", "B2", "B3")                  // 사무실: B1~B3
        val homeFloors = listOf("B1", "B2", "B3", "B4", "B5")        // 집: B1~B5

        fun bindSpinner(spinner: Spinner, items: List<String>) {
            val adapter = ArrayAdapter(
                this,
                android.R.layout.simple_spinner_item,
                items
            )
            adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
            spinner.adapter = adapter
        }

        bindSpinner(spOfficeSeltos, officeFloors)
        bindSpinner(spHomeSeltos, homeFloors)
        bindSpinner(spHomeG90, homeFloors)

        // 저장된 값 복원
        lifecycleScope.launch {
            val prefs = dataStore.data.first()

            val officeIndex = prefs[KEY_OFFICE_SELTOS] ?: 0
            val homeSeltosIndex = prefs[KEY_HOME_SELTOS] ?: 0
            val homeG90Index = prefs[KEY_HOME_G90] ?: 0
            val lastSaved = prefs[KEY_LAST_SAVED] ?: "-"

            // 범위 안전 처리
            spOfficeSeltos.setSelection(officeIndex.coerceIn(0, officeFloors.lastIndex))
            spHomeSeltos.setSelection(homeSeltosIndex.coerceIn(0, homeFloors.lastIndex))
            spHomeG90.setSelection(homeG90Index.coerceIn(0, homeFloors.lastIndex))

            tvLastSaved.text = "마지막 저장: $lastSaved"
        }

        btnSave.setOnClickListener {
            val officeIndex = spOfficeSeltos.selectedItemPosition
            val homeSeltosIndex = spHomeSeltos.selectedItemPosition
            val homeG90Index = spHomeG90.selectedItemPosition

            val now = LocalDateTime.now()
            val formatted = now.format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm"))

            lifecycleScope.launch {
                dataStore.edit { prefs ->
                    prefs[KEY_OFFICE_SELTOS] = officeIndex
                    prefs[KEY_HOME_SELTOS] = homeSeltosIndex
                    prefs[KEY_HOME_G90] = homeG90Index
                    prefs[KEY_LAST_SAVED] = formatted
                }
                tvLastSaved.text = "마지막 저장: $formatted"
            }
        }
    }
}

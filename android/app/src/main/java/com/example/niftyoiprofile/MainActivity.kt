package com.example.niftyoiprofile

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.launch

private val Navy = Color(0xFF0B1220)
private val CardBg = Color(0xFF172337)
private val Green = Color(0xFF20C997)
private val Red = Color(0xFFFF647C)
private val Amber = Color(0xFFFFC857)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { MaterialTheme(colorScheme = darkColorScheme()) { Dashboard() } }
    }
}

@Composable
fun Dashboard() {
    var baseUrl by remember { mutableStateOf("http://10.0.2.2:8000/") }
    var strike by remember { mutableStateOf("25350") }
    var expiry by remember { mutableStateOf("") }
    var side by remember { mutableStateOf("PE") }
    var status by remember { mutableStateOf("Not connected") }
    var provider by remember { mutableStateOf("Checking Dhan…") }
    var dataMode by remember { mutableStateOf("—") }
    var dhanConnected by remember { mutableStateOf(false) }
    var ltp by remember { mutableStateOf("--") }
    var oi by remember { mutableStateOf("--") }
    var underlyingLtp by remember { mutableStateOf("--") }
    var buckets by remember { mutableStateOf(emptyList<BucketDto>()) }
    var error by remember { mutableStateOf("") }
    var info by remember { mutableStateOf("") }
    val scope = rememberCoroutineScope()

    fun refreshStatus() {
        scope.launch {
            try {
                val api = ApiClient.create(baseUrl)
                val h = api.health()
                status = h.status
                dataMode = h.data_mode.ifBlank { "demo" }
                dhanConnected = h.dhan_connected
                val p = api.providerStatus()
                provider = "${p.provider} · ${p.mode} · ${p.message}"
                error = ""
            } catch (e: Exception) {
                error = e.message ?: "Backend unreachable"
                status = "offline"
                dhanConnected = false
            }
        }
    }

    fun loadProfile() {
        scope.launch {
            try {
                val api = ApiClient.create(baseUrl)
                if (expiry.isBlank()) {
                    error = "Set expiry (YYYY-MM-DD) first, or use Fetch from Dhan"
                    return@launch
                }
                val key = "NIFTY|$expiry|$strike|$side"
                val profile = api.contractProfile(key, 10.0)
                ltp = profile.latest?.ltp?.toString() ?: "--"
                oi = profile.latest?.oi?.toString() ?: "--"
                buckets = profile.profile
                error = ""
                info = "Loaded local profile for $key"
            } catch (e: Exception) {
                error = e.message ?: "Profile load failed"
            }
        }
    }

    fun fetchFromDhan() {
        scope.launch {
            try {
                info = "Fetching option chain from DhanHQ…"
                error = ""
                val api = ApiClient.create(baseUrl)
                val chain = api.dhanOptionChain(
                    underlying = "NIFTY",
                    expiry = expiry,
                    atmRange = 10,
                    ingest = true
                )
                underlyingLtp = chain.underlying_ltp.toString()
                if (expiry.isBlank() && chain.expiry.isNotBlank()) {
                    expiry = chain.expiry
                }
                info = "Dhan: ${chain.contract_count} contracts, ingested ${chain.ingested} · expiry ${chain.expiry}"
                // Reload profile for selected strike after ingest
                val key = "NIFTY|${chain.expiry}|$strike|$side"
                val profile = api.contractProfile(key, 10.0)
                ltp = profile.latest?.ltp?.toString() ?: "--"
                oi = profile.latest?.oi?.toString() ?: "--"
                buckets = profile.profile
                refreshStatus()
            } catch (e: Exception) {
                error = e.message ?: "Dhan fetch failed"
                info = "Ensure backend DATA_MODE=live and valid DHAN credentials + Data API plan"
            }
        }
    }

    LaunchedEffect(Unit) { refreshStatus() }

    Column(
        Modifier
            .fillMaxSize()
            .background(Navy)
            .verticalScroll(rememberScrollState())
            .padding(16.dp)
    ) {
        Text("NIFTY OI Premium Profile", color = Color.White, fontSize = 20.sp)
        Text("DhanHQ Data API · ATM ± 10 · Premium-wise OI", color = Color.LightGray, fontSize = 12.sp)
        Spacer(Modifier.height(12.dp))

        Card(colors = CardDefaults.cardColors(containerColor = CardBg)) {
            Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(
                    value = baseUrl,
                    onValueChange = { baseUrl = it },
                    label = { Text("Backend URL") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(
                        value = strike,
                        onValueChange = { strike = it },
                        label = { Text("Strike") },
                        singleLine = true,
                        modifier = Modifier.weight(1f)
                    )
                    OutlinedTextField(
                        value = side,
                        onValueChange = { side = it.uppercase().take(2) },
                        label = { Text("CE/PE") },
                        singleLine = true,
                        modifier = Modifier.weight(0.6f)
                    )
                }
                OutlinedTextField(
                    value = expiry,
                    onValueChange = { expiry = it },
                    label = { Text("Expiry YYYY-MM-DD (blank = nearest from Dhan)") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(onClick = { refreshStatus() }) { Text("Status") }
                    Button(onClick = { loadProfile() }) { Text("Load profile") }
                    Button(
                        onClick = { fetchFromDhan() },
                        colors = ButtonDefaults.buttonColors(
                            containerColor = if (dhanConnected) Green else Amber
                        )
                    ) { Text("Fetch Dhan") }
                }
                Text(
                    "Backend: $status  ·  mode: $dataMode  ·  Dhan: ${if (dhanConnected) "CONNECTED" else "NOT CONNECTED"}",
                    color = if (dhanConnected) Green else Amber,
                    fontSize = 12.sp
                )
                Text(provider, color = Color.LightGray, fontSize = 11.sp)
                if (info.isNotBlank()) Text(info, color = Green, fontSize = 11.sp)
                if (error.isNotBlank()) Text(error, color = Red, fontSize = 11.sp)
            }
        }

        Spacer(Modifier.height(12.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            MetricCard("Underlying", underlyingLtp, Modifier.weight(1f))
            MetricCard("LTP", ltp, Modifier.weight(1f))
            MetricCard("Current OI", oi, Modifier.weight(1f))
        }

        Spacer(Modifier.height(12.dp))
        Card(colors = CardDefaults.cardColors(containerColor = CardBg)) {
            Column(Modifier.padding(14.dp)) {
                Text("NIFTY $strike $side · Premium-wise OI profile", color = Color.White)
                Text("Premium bucket | Net OI | Fresh / Unwinding", color = Color.LightGray, fontSize = 10.sp)
                Spacer(Modifier.height(10.dp))
                if (buckets.isEmpty()) {
                    Text(
                        "No OI events yet. Configure Dhan credentials on backend, set DATA_MODE=live, then tap Fetch Dhan.",
                        color = Color.LightGray,
                        fontSize = 12.sp
                    )
                } else {
                    buckets.forEach { b ->
                        Row(
                            Modifier.fillMaxWidth().padding(vertical = 5.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                "${b.premium_from.toInt()}–${b.premium_to.toInt()}",
                                Modifier.width(70.dp),
                                color = Color.LightGray,
                                fontSize = 11.sp
                            )
                            Text(
                                "${b.net_oi}",
                                Modifier.weight(1f),
                                color = if (b.net_oi >= 0) Green else Red,
                                fontSize = 12.sp
                            )
                            Text("+${b.fresh_oi} / -${b.unwinding}", color = Color.LightGray, fontSize = 10.sp)
                        }
                    }
                }
            }
        }

        Spacer(Modifier.height(12.dp))
        Card(colors = CardDefaults.cardColors(containerColor = CardBg)) {
            Column(Modifier.padding(14.dp)) {
                Text("Dhan setup (backend only)", color = Color.White)
                Text(
                    "1. web.dhan.co → Profile → Access DhanHQ APIs\n" +
                    "2. Generate Access Token + enable Data APIs plan\n" +
                    "3. backend/.env → DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN, DATA_MODE=live\n" +
                    "4. Never put tokens in this APK\n" +
                    "5. Option chain rate limit: 1 request / 3 seconds",
                    color = Color.LightGray,
                    fontSize = 11.sp
                )
            }
        }
    }
}

@Composable
fun MetricCard(label: String, value: String, modifier: Modifier = Modifier) {
    Card(modifier, colors = CardDefaults.cardColors(containerColor = CardBg)) {
        Column(Modifier.padding(14.dp)) {
            Text(label, color = Color.LightGray, fontSize = 11.sp)
            Text(value, color = Color.White, fontSize = 18.sp)
        }
    }
}

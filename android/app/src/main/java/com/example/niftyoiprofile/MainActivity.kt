package com.example.niftyoiprofile

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
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
    var expiry by remember { mutableStateOf("YYYY-MM-DD") }
    var side by remember { mutableStateOf("PE") }
    var status by remember { mutableStateOf("Not connected") }
    var provider by remember { mutableStateOf("Dhan adapter not configured") }
    var ltp by remember { mutableStateOf("--") }
    var oi by remember { mutableStateOf("--") }
    var buckets by remember { mutableStateOf(emptyList<BucketDto>()) }
    var error by remember { mutableStateOf("") }
    val scope = rememberCoroutineScope()

    fun load() {
        scope.launch {
            try {
                val api = ApiClient.create(baseUrl)
                status = api.health().status
                val p = api.providerStatus()
                provider = "${p.provider}: ${p.message}"
                val key = "NIFTY|$expiry|$strike|$side"
                val profile = api.contractProfile(key, 10.0)
                ltp = profile.latest?.ltp?.toString() ?: "--"
                oi = profile.latest?.oi?.toString() ?: "--"
                buckets = profile.profile
                error = ""
            } catch (e: Exception) {
                error = e.message ?: "Connection failed"
            }
        }
    }

    Column(Modifier.fillMaxSize().background(Navy).verticalScroll(rememberScrollState()).padding(16.dp)) {
        Text("NIFTY OI PREMIUM PROFILE", color = Color.White, fontSize = 20.sp)
        Text("Strike-wise · Premium-wise · CE / PE", color = Color.LightGray, fontSize = 12.sp)
        Spacer(Modifier.height(14.dp))
        Card(colors = CardDefaults.cardColors(containerColor = CardBg)) {
            Column(Modifier.padding(12.dp)) {
                OutlinedTextField(baseUrl, { baseUrl = it }, label = { Text("Backend URL") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(strike, { strike = it.filter(Char::isDigit) }, label = { Text("Strike") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(expiry, { expiry = it }, label = { Text("Expiry YYYY-MM-DD") }, modifier = Modifier.fillMaxWidth())
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    FilterChip(selected = side == "CE", onClick = { side = "CE" }, label = { Text("CE") })
                    FilterChip(selected = side == "PE", onClick = { side = "PE" }, label = { Text("PE") })
                    Button(onClick = { load() }) { Text("Load profile") }
                }
                Text("Backend: $status", color = Green, fontSize = 12.sp)
                Text(provider, color = Color.LightGray, fontSize = 11.sp)
                if (error.isNotBlank()) Text(error, color = Red, fontSize = 11.sp)
            }
        }
        Spacer(Modifier.height(12.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            MetricCard("LTP", ltp, Modifier.weight(1f))
            MetricCard("Current OI", oi, Modifier.weight(1f))
        }
        Spacer(Modifier.height(12.dp))
        Card(colors = CardDefaults.cardColors(containerColor = CardBg)) {
            Column(Modifier.padding(14.dp)) {
                Text("NIFTY $strike $side · Premium-wise OI profile", color = Color.White)
                Text("Premium bucket | Fresh OI | Unwinding | Net OI", color = Color.LightGray, fontSize = 10.sp)
                Spacer(Modifier.height(10.dp))
                if (buckets.isEmpty()) {
                    Text("No stored OI events for this contract. Connect a verified data provider and ingest snapshots.", color = Color.LightGray, fontSize = 12.sp)
                } else buckets.forEach { b ->
                    Row(Modifier.fillMaxWidth().padding(vertical = 5.dp), verticalAlignment = Alignment.CenterVertically) {
                        Text("${b.premium_from.toInt()}–${b.premium_to.toInt()}", Modifier.width(65.dp), color = Color.LightGray, fontSize = 11.sp)
                        Text("${b.net_oi}", Modifier.weight(1f), color = if (b.net_oi >= 0) Green else Red, fontSize = 12.sp)
                        Text("+${b.fresh_oi} / -${b.unwinding}", color = Color.LightGray, fontSize = 10.sp)
                    }
                }
            }
        }
        Spacer(Modifier.height(12.dp))
        Card(colors = CardDefaults.cardColors(containerColor = CardBg)) {
            Column(Modifier.padding(14.dp)) {
                Text("Additional modules", color = Color.White)
                Text("Strike CE/PE profile · Candlestick OHLCV · Footprint/order flow · Strike × premium heatmap · Developing POC/VAH/VAL",
                    color = Color.LightGray, fontSize = 12.sp)
                Text("Footprint requires trade prints and aggressor-side data; market depth alone is insufficient.",
                    color = Color(0xFFFFC857), fontSize = 10.sp)
            }
        }
    }
}

@Composable
fun MetricCard(label: String, value: String, modifier: Modifier = Modifier) {
    Card(modifier, colors = CardDefaults.cardColors(containerColor = CardBg)) {
        Column(Modifier.padding(14.dp)) {
            Text(label, color = Color.LightGray, fontSize = 11.sp)
            Text(value, color = Color.White, fontSize = 19.sp)
        }
    }
}

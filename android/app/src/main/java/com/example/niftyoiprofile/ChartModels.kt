package com.example.niftyoiprofile

// UI chart contract models. Integrate a selected open-source renderer
// (e.g. TradingView Lightweight Charts in WebView) for production candles.
data class OhlcBar(val time: Long, val open: Double, val high: Double,
                   val low: Double, val close: Double, val volume: Long)

data class FootprintLevel(val price: Double, val bidVolume: Long,
                          val askVolume: Long, val unknownVolume: Long) {
    val delta: Long get() = askVolume - bidVolume
}

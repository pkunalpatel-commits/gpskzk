package com.example.niftyoiprofile

import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.GET
import retrofit2.http.Query

data class HealthDto(
    val status: String = "",
    val data_mode: String = "",
    val dhan_connected: Boolean = false
)

data class ProviderDto(
    val provider: String = "",
    val configured: Boolean = false,
    val mode: String = "",
    val message: String = "",
    val connected: Boolean = false,
    val last_error: String = ""
)

data class LatestDto(
    val timestamp: String = "",
    val ltp: Double = 0.0,
    val oi: Long = 0,
    val volume: Long = 0,
    val strike: Int = 0,
    val option_type: String = "",
    val expiry: String = ""
)

data class BucketDto(
    val premium_from: Double = 0.0,
    val premium_to: Double = 0.0,
    val fresh_oi: Long = 0,
    val unwinding: Long = 0,
    val net_oi: Long = 0
)

data class ContractProfileDto(
    val contract_key: String = "",
    val latest: LatestDto? = null,
    val bucket_size: Double = 10.0,
    val profile: List<BucketDto> = emptyList()
)

data class OptionChainResponse(
    val underlying: String = "",
    val expiry: String = "",
    val underlying_ltp: Double = 0.0,
    val source: String = "",
    val fetched_at: String = "",
    val contract_count: Int = 0,
    val ingested: Int = 0
)

data class ExpiryListDto(
    val underlying: String = "",
    val expiries: List<String> = emptyList(),
    val source: String = ""
)

interface OiApi {
    @GET("health")
    suspend fun health(): HealthDto

    @GET("api/v1/provider/status")
    suspend fun providerStatus(): ProviderDto

    @GET("api/v1/profile/contract")
    suspend fun contractProfile(
        @Query("contract_key") contractKey: String,
        @Query("bucket_size") bucketSize: Double = 10.0
    ): ContractProfileDto

    @GET("api/v1/dhan/expiries")
    suspend fun dhanExpiries(
        @Query("underlying") underlying: String = "NIFTY"
    ): ExpiryListDto

    @GET("api/v1/dhan/optionchain")
    suspend fun dhanOptionChain(
        @Query("underlying") underlying: String = "NIFTY",
        @Query("expiry") expiry: String = "",
        @Query("atm_range") atmRange: Int = 10,
        @Query("ingest") ingest: Boolean = true
    ): OptionChainResponse
}

object ApiClient {
    fun create(baseUrl: String): OiApi = Retrofit.Builder()
        .baseUrl(if (baseUrl.endsWith("/")) baseUrl else "$baseUrl/")
        .addConverterFactory(GsonConverterFactory.create())
        .build()
        .create(OiApi::class.java)
}

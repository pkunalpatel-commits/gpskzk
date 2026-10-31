package com.example.niftyoiprofile

import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.GET
import retrofit2.http.Query

data class HealthDto(val status: String = "")
data class ProviderDto(val provider: String = "", val configured: Boolean = false,
                       val mode: String = "", val message: String = "")
data class LatestDto(val timestamp: String, val ltp: Double, val oi: Long,
                     val volume: Long, val strike: Int, val option_type: String, val expiry: String)
data class BucketDto(val premium_from: Double, val premium_to: Double,
                     val fresh_oi: Long, val unwinding: Long, val net_oi: Long)
data class ContractProfileDto(val contract_key: String, val latest: LatestDto?,
                               val bucket_size: Double, val profile: List<BucketDto>)

interface OiApi {
    @GET("health") suspend fun health(): HealthDto
    @GET("api/v1/provider/status") suspend fun providerStatus(): ProviderDto
    @GET("api/v1/profile/contract") suspend fun contractProfile(
        @Query("contract_key") contractKey: String,
        @Query("bucket_size") bucketSize: Double = 10.0
    ): ContractProfileDto
}

object ApiClient {
    fun create(baseUrl: String): OiApi = Retrofit.Builder()
        .baseUrl(if (baseUrl.endsWith("/")) baseUrl else "$baseUrl/")
        .addConverterFactory(GsonConverterFactory.create())
        .build().create(OiApi::class.java)
}

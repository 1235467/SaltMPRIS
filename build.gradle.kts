plugins {
    id("java-library")
    kotlin("jvm") version "1.9.22"
    kotlin("kapt") version "1.9.22"
    kotlin("plugin.serialization") version "1.9.22"
}

group = "com.mpris.saltplayer"
version = "1.0.0"

repositories {
    mavenCentral()
    maven("https://jitpack.io")
}

java {
    sourceCompatibility = JavaVersion.VERSION_21
    targetCompatibility = JavaVersion.VERSION_21
}

tasks.withType<org.jetbrains.kotlin.gradle.tasks.KotlinCompile> {
    compilerOptions {
        jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_21)
    }
}

dependencies {
    compileOnly(kotlin("stdlib"))
    compileOnly("com.github.Moriafly:spw-workshop-api:0.1.0-dev14")
    kapt("com.github.Moriafly:spw-workshop-api:0.1.0-dev14")

    // HTTP server
    implementation("io.ktor:ktor-server-core:2.3.7")
    implementation("io.ktor:ktor-server-netty:2.3.7")
    implementation("io.ktor:ktor-server-content-negotiation:2.3.7")
    implementation("io.ktor:ktor-serialization-kotlinx-json:2.3.7")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.2")
}

val pluginClass = "com.mpris.saltplayer.MprisPlugin"
val pluginId = "saltplayer-mpris"
val pluginVersion = "1.0.0"
val pluginProvider = "MPRIS Bridge"

tasks.named<Jar>("jar") {
    manifest {
        attributes["Plugin-Class"] = pluginClass
        attributes["Plugin-Id"] = pluginId
        attributes["Plugin-Version"] = pluginVersion
        attributes["Plugin-Provider"] = pluginProvider
        attributes["Plugin-Name"] = "MPRIS Bridge Plugin"
        attributes["Plugin-Description"] = "Exposes playback info via HTTP for MPRIS integration"
    }
}

tasks.register<Jar>("plugin") {
    archiveBaseName.set("plugin-$pluginId-$pluginVersion")

    into("classes") {
        with(tasks.named<Jar>("jar").get())
    }
    dependsOn(configurations.runtimeClasspath)
    into("lib") {
        from({
            configurations.runtimeClasspath.get()
                .filter { it.name.endsWith("jar") }
        })
    }
    archiveExtension.set("zip")
}

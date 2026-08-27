# Android build environment gate

## Observed local failure

On 2026-08-26, Java and the Gradle wrapper were available:

- Microsoft OpenJDK `21.0.12`.
- Gradle wrapper `9.5.0`.
- `gradlew.bat --version` succeeds.

Initially, build tasks failed before project evaluation with:

```text
java.io.IOException: Unable to establish loopback connection
```

The failure reproduced for both the full app and the isolated funding module,
including with `--no-daemon`, `-Djava.net.preferIPv4Stack=true`, and empty
`org.gradle.jvmargs`. It is resolved on this workstation by setting
`JAVA_TOOL_OPTIONS` as described below.

## Verification commands

From `android/`:

```powershell
./gradlew.bat --version
./gradlew.bat --no-daemon testDebugUnitTest lintDebug
./gradlew.bat --no-daemon :features:funding:compileDebugKotlin
```

The first command is expected to pass. On this workstation, set the following
workaround before the latter commands:

```powershell
New-Item -ItemType Directory -Path C:\Temp\peti-java-sockets -Force | Out-Null
$env:JAVA_TOOL_OPTIONS = '-Djdk.net.unixdomain.tmpdir=C:\Temp\peti-java-sockets'
```

With that setting, `:features:funding:compileDebugKotlin`,
`testDebugUnitTest`, `lintDebug`, and `assembleDebug` have completed
successfully.

## Remediation checklist

1. Check Windows Firewall/endpoint security rules for `java.exe` and
   `gradle-daemon` loopback traffic.
2. Stop stale Gradle/Java processes and retry the commands above.
3. Retry with a clean Gradle user home on a host where loopback is allowed.
4. Record successful `testDebugUnitTest`, `lintDebug`, and `assembleDebug`
   output before promoting the Android gate.

## Root cause/workaround

Java's Windows NIO `PipeImpl` can otherwise fail with `Unable to establish
loopback connection` while Gradle starts its daemon. The setting above points
Java's Unix-domain-socket temporary directory at a native Windows directory.
It is an environment workaround and does not change application behavior.

pluginManagement { repositories { google(); mavenCentral(); gradlePluginPortal() } }
dependencyResolutionManagement { repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS); repositories { google(); mavenCentral() } }
rootProject.name = "PETi"
include(":app")
include(":core:common")
include(":core:model")
include(":core:network")
include(":core:ui")
include(":core:testing")
include(":features:funding")

; Make API
core = 7.x
api = 2

; Core
projects[drupal][version] = "7.38"
projects[drupal][type] = core

; Defaults
defaults[projects][subdir] = contrib
defaults[projects][l10n_url] = http://ftp.drupal.org/files/translations/l10n_server.xml

; Modules
projects[admin_menu][version] = "3.0-rc5"
projects[adminimal_admin_menu][version] = "1.6"
projects[ckeditor][version] = "1.16"
projects[ctools][version] = "1.7"
projects[date][version] = "2.8"
projects[devel][version] = "1.5"
projects[diff][version] = "3.2"
projects[email][version] = "1.3"
projects[entity][version] = "1.6"
projects[entityreference][version] = "1.1"
projects[features][version] = "2.5"
projects[features_orphans][version] = "1.2"
projects[field_group][version] = "1.4"
projects[honeypot][version] = "1.19"
projects[i18n][version] = "1.13"
projects[jquery_update][version] = "2.6"
projects[libraries][version] = "2.2"
projects[link][version] = "1.3"
projects[media][version] = "1.5"
projects[module_filter][version] = "2.0"
projects[pathauto][version] = "1.2"
projects[pathauto][patch][] = "http://drupal.org/files/pathauto-persist-936222-130-pathauto-state.patch"
projects[strongarm][version] = "2.0"
projects[token][version] = "1.6"
projects[transliteration][version] = "3.2"
projects[variable][version] = "2.5"
projects[views][version] = "3.11"
projects[views_load_more][version] = "1.5"

; Themes
projects[adminimal_theme][version] = "1.21"
projects[adminimal_theme][subdir] = ""

; Libraries
;libraries[ckeditor][download][type] = git
;libraries[ckeditor][download][url] = https://github.com/ckeditor/ckeditor-releases.git
;libraries[ckeditor][download][tag] = 4.5.1
;libraries[ckeditor][type] = "library"


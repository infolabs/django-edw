--
-- Скрипт сгенерирован Devart dbForge Studio for MySQL, Версия 7.2.34.0
-- Домашняя страница продукта: http://www.devart.com/ru/dbforge/mysql/studio
-- Дата скрипта: 24.11.2016 17:42:18
-- Версия сервера: 5.6.28
-- Версия клиента: 4.1
--


--
-- Описание для базы данных edw_todos_db
--
DROP DATABASE IF EXISTS edw_todos_db;
CREATE DATABASE edw_todos_db
	CHARACTER SET utf8
	COLLATE utf8_general_ci;

-- 
-- Отключение внешних ключей
-- 
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;

-- 
-- Установить режим SQL (SQL mode)
-- 
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;

-- 
-- Установка кодировки, с использованием которой клиент будет посылать запросы на сервер
--
SET NAMES 'utf8';

-- 
-- Установка базы данных по умолчанию
--
USE edw_todos_db;

--
-- Описание для таблицы auth_group
--
CREATE TABLE auth_group (
  id INT(11) NOT NULL AUTO_INCREMENT,
  name VARCHAR(80) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE INDEX name (name)
)
ENGINE = INNODB
AUTO_INCREMENT = 1
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы auth_user
--
CREATE TABLE auth_user (
  id INT(11) NOT NULL AUTO_INCREMENT,
  password VARCHAR(128) NOT NULL,
  last_login DATETIME(6) DEFAULT NULL,
  is_superuser TINYINT(1) NOT NULL,
  username VARCHAR(30) NOT NULL,
  first_name VARCHAR(30) NOT NULL,
  last_name VARCHAR(30) NOT NULL,
  email VARCHAR(254) NOT NULL,
  is_staff TINYINT(1) NOT NULL,
  is_active TINYINT(1) NOT NULL,
  date_joined DATETIME(6) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE INDEX username (username)
)
ENGINE = INNODB
AUTO_INCREMENT = 4
AVG_ROW_LENGTH = 16384
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы django_content_type
--
CREATE TABLE django_content_type (
  id INT(11) NOT NULL AUTO_INCREMENT,
  app_label VARCHAR(100) NOT NULL,
  model VARCHAR(100) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE INDEX django_content_type_app_label_76bd3d3b_uniq (app_label, model)
)
ENGINE = INNODB
AUTO_INCREMENT = 36
AVG_ROW_LENGTH = 585
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы django_migrations
--
CREATE TABLE django_migrations (
  id INT(11) NOT NULL AUTO_INCREMENT,
  app VARCHAR(255) NOT NULL,
  name VARCHAR(255) NOT NULL,
  applied DATETIME(6) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB
AUTO_INCREMENT = 41
AVG_ROW_LENGTH = 528
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы django_session
--
CREATE TABLE django_session (
  session_key VARCHAR(40) NOT NULL,
  session_data LONGTEXT NOT NULL,
  expire_date DATETIME(6) NOT NULL,
  PRIMARY KEY (session_key),
  INDEX django_session_de54fa62 (expire_date)
)
ENGINE = INNODB
AVG_ROW_LENGTH = 963
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы django_site
--
CREATE TABLE django_site (
  id INT(11) NOT NULL AUTO_INCREMENT,
  domain VARCHAR(100) NOT NULL,
  name VARCHAR(50) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE INDEX django_site_domain_a2e37b91_uniq (domain)
)
ENGINE = INNODB
AUTO_INCREMENT = 2
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы easy_thumbnails_source
--
CREATE TABLE easy_thumbnails_source (
  id INT(11) NOT NULL AUTO_INCREMENT,
  storage_hash VARCHAR(40) NOT NULL,
  name VARCHAR(255) NOT NULL,
  modified DATETIME(6) NOT NULL,
  PRIMARY KEY (id),
  INDEX easy_thumbnails_source_b068931c (name),
  INDEX easy_thumbnails_source_b454e115 (storage_hash),
  UNIQUE INDEX easy_thumbnails_source_storage_hash_481ce32d_uniq (storage_hash, name)
)
ENGINE = INNODB
AUTO_INCREMENT = 1
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы filer_thumbnailoption
--
CREATE TABLE filer_thumbnailoption (
  id INT(11) NOT NULL AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL,
  width INT(11) NOT NULL,
  height INT(11) NOT NULL,
  crop TINYINT(1) NOT NULL,
  upscale TINYINT(1) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB
AUTO_INCREMENT = 1
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы post_office_attachment
--
CREATE TABLE post_office_attachment (
  id INT(11) NOT NULL AUTO_INCREMENT,
  file VARCHAR(100) NOT NULL,
  name VARCHAR(255) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB
AUTO_INCREMENT = 1
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы post_office_emailtemplate
--
CREATE TABLE post_office_emailtemplate (
  id INT(11) NOT NULL AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL,
  description LONGTEXT NOT NULL,
  subject VARCHAR(255) NOT NULL,
  content LONGTEXT NOT NULL,
  html_content LONGTEXT NOT NULL,
  created DATETIME(6) NOT NULL,
  last_updated DATETIME(6) NOT NULL,
  default_template_id INT(11) DEFAULT NULL,
  language VARCHAR(12) NOT NULL,
  PRIMARY KEY (id),
  INDEX post_office_emailtemplate_dea6f63e (default_template_id),
  UNIQUE INDEX post_office_emailtemplate_language_ed7b1d39_uniq (language, default_template_id),
  CONSTRAINT pos_default_template_id_2ac2f889_fk_post_office_emailtemplate_id FOREIGN KEY (default_template_id)
    REFERENCES post_office_emailtemplate(id) ON DELETE RESTRICT ON UPDATE RESTRICT
)
ENGINE = INNODB
AUTO_INCREMENT = 1
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы todos_term
--
CREATE TABLE todos_term (
  id INT(11) NOT NULL AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL,
  slug VARCHAR(50) NOT NULL,
  path VARCHAR(255) NOT NULL,
  semantic_rule SMALLINT(5) UNSIGNED NOT NULL,
  attributes BIGINT(20) DEFAULT NULL,
  specification_mode SMALLINT(5) UNSIGNED NOT NULL,
  created_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL,
  view_class VARCHAR(255) DEFAULT NULL,
  description LONGTEXT DEFAULT NULL,
  active TINYINT(1) NOT NULL,
  system_flags BIGINT(20) DEFAULT NULL,
  lft INT(10) UNSIGNED NOT NULL,
  rght INT(10) UNSIGNED NOT NULL,
  tree_id INT(10) UNSIGNED NOT NULL,
  level INT(10) UNSIGNED NOT NULL,
  parent_id INT(11) DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE INDEX path (path),
  INDEX todos_term_2dbcba41 (slug),
  INDEX todos_term_3cfbd988 (rght),
  INDEX todos_term_656442a0 (tree_id),
  INDEX todos_term_6be37982 (parent_id),
  INDEX todos_term_c76a5e84 (active),
  INDEX todos_term_c9e9a848 (level),
  INDEX todos_term_caf7cc51 (lft),
  CONSTRAINT todos_term_parent_id_b1624525_fk_todos_term_id FOREIGN KEY (parent_id)
    REFERENCES todos_term(id) ON DELETE RESTRICT ON UPDATE RESTRICT
)
ENGINE = INNODB
AUTO_INCREMENT = 76
AVG_ROW_LENGTH = 224
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы auth_permission
--
CREATE TABLE auth_permission (
  id INT(11) NOT NULL AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL,
  content_type_id INT(11) NOT NULL,
  codename VARCHAR(100) NOT NULL,
  PRIMARY KEY (id),
  INDEX auth_permission_417f1b1c (content_type_id),
  UNIQUE INDEX auth_permission_content_type_id_01ab375a_uniq (content_type_id, codename),
  CONSTRAINT auth_permissi_content_type_id_2f476e4b_fk_django_content_type_id FOREIGN KEY (content_type_id)
    REFERENCES django_content_type(id) ON DELETE RESTRICT ON UPDATE RESTRICT
)
ENGINE = INNODB
AUTO_INCREMENT = 104
AVG_ROW_LENGTH = 192
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы auth_user_groups
--
CREATE TABLE auth_user_groups (
  id INT(11) NOT NULL AUTO_INCREMENT,
  user_id INT(11) NOT NULL,
  group_id INT(11) NOT NULL,
  PRIMARY KEY (id),
  INDEX auth_user_groups_0e939a4f (group_id),
  INDEX auth_user_groups_e8701ad4 (user_id),
  UNIQUE INDEX auth_user_groups_user_id_94350c0c_uniq (user_id, group_id),
  CONSTRAINT auth_user_groups_group_id_97559544_fk_auth_group_id FOREIGN KEY (group_id)
    REFERENCES auth_group(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT auth_user_groups_user_id_6a12ed8b_fk_auth_user_id FOREIGN KEY (user_id)
    REFERENCES auth_user(id) ON DELETE RESTRICT ON UPDATE RESTRICT
)
ENGINE = INNODB
AUTO_INCREMENT = 1
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы authtoken_token
--
CREATE TABLE authtoken_token (
  `key` VARCHAR(40) NOT NULL,
  created DATETIME(6) NOT NULL,
  user_id INT(11) NOT NULL,
  PRIMARY KEY (`key`),
  UNIQUE INDEX user_id (user_id),
  CONSTRAINT authtoken_token_user_id_35299eff_fk_auth_user_id FOREIGN KEY (user_id)
    REFERENCES auth_user(id) ON DELETE RESTRICT ON UPDATE RESTRICT
)
ENGINE = INNODB
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы django_admin_log
--
CREATE TABLE django_admin_log (
  id INT(11) NOT NULL AUTO_INCREMENT,
  action_time DATETIME(6) NOT NULL,
  object_id LONGTEXT DEFAULT NULL,
  object_repr VARCHAR(200) NOT NULL,
  action_flag SMALLINT(5) UNSIGNED NOT NULL,
  change_message LONGTEXT NOT NULL,
  content_type_id INT(11) DEFAULT NULL,
  user_id INT(11) NOT NULL,
  PRIMARY KEY (id),
  INDEX django_admin_log_417f1b1c (content_type_id),
  INDEX django_admin_log_e8701ad4 (user_id),
  CONSTRAINT django_admin__content_type_id_c4bce8eb_fk_django_content_type_id FOREIGN KEY (content_type_id)
    REFERENCES django_content_type(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT django_admin_log_user_id_c564eba6_fk_auth_user_id FOREIGN KEY (user_id)
    REFERENCES auth_user(id) ON DELETE RESTRICT ON UPDATE RESTRICT
)
ENGINE = INNODB
AUTO_INCREMENT = 103
AVG_ROW_LENGTH = 264
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы easy_thumbnails_thumbnail
--
CREATE TABLE easy_thumbnails_thumbnail (
  id INT(11) NOT NULL AUTO_INCREMENT,
  storage_hash VARCHAR(40) NOT NULL,
  name VARCHAR(255) NOT NULL,
  modified DATETIME(6) NOT NULL,
  source_id INT(11) NOT NULL,
  PRIMARY KEY (id),
  INDEX easy_thumbnails_thumbnail_b068931c (name),
  INDEX easy_thumbnails_thumbnail_b454e115 (storage_hash),
  UNIQUE INDEX easy_thumbnails_thumbnail_storage_hash_fb375270_uniq (storage_hash, name, source_id),
  CONSTRAINT easy_thumbnails__source_id_5b57bc77_fk_easy_thumbnails_source_id FOREIGN KEY (source_id)
    REFERENCES easy_thumbnails_source(id) ON DELETE RESTRICT ON UPDATE RESTRICT
)
ENGINE = INNODB
AUTO_INCREMENT = 1
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы filer_clipboard
--
CREATE TABLE filer_clipboard (
  id INT(11) NOT NULL AUTO_INCREMENT,
  user_id INT(11) NOT NULL,
  PRIMARY KEY (id),
  INDEX filer_clipboard_e8701ad4 (user_id),
  CONSTRAINT filer_clipboard_user_id_b52ff0bc_fk_auth_user_id FOREIGN KEY (user_id)
    REFERENCES auth_user(id) ON DELETE RESTRICT ON UPDATE RESTRICT
)
ENGINE = INNODB
AUTO_INCREMENT = 2
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы filer_folder
--
CREATE TABLE filer_folder (
  id INT(11) NOT NULL AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL,
  uploaded_at DATETIME(6) NOT NULL,
  created_at DATETIME(6) NOT NULL,
  modified_at DATETIME(6) NOT NULL,
  lft INT(10) UNSIGNED NOT NULL,
  rght INT(10) UNSIGNED NOT NULL,
  tree_id INT(10) UNSIGNED NOT NULL,
  level INT(10) UNSIGNED NOT NULL,
  owner_id INT(11) DEFAULT NULL,
  parent_id INT(11) DEFAULT NULL,
  PRIMARY KEY (id),
  INDEX filer_folder_3cfbd988 (rght),
  INDEX filer_folder_656442a0 (tree_id),
  INDEX filer_folder_c9e9a848 (level),
  INDEX filer_folder_caf7cc51 (lft),
  UNIQUE INDEX filer_folder_parent_id_bc773258_uniq (parent_id, name),
  CONSTRAINT filer_folder_owner_id_be530fb4_fk_auth_user_id FOREIGN KEY (owner_id)
    REFERENCES auth_user(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT filer_folder_parent_id_308aecda_fk_filer_folder_id FOREIGN KEY (parent_id)
    REFERENCES filer_folder(id) ON DELETE RESTRICT ON UPDATE RESTRICT
)
ENGINE = INNODB
AUTO_INCREMENT = 1
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы post_office_email
--
CREATE TABLE post_office_email (
  id INT(11) NOT NULL AUTO_INCREMENT,
  from_email VARCHAR(254) NOT NULL,
  `to` LONGTEXT NOT NULL,
  cc LONGTEXT NOT NULL,
  bcc LONGTEXT NOT NULL,
  subject VARCHAR(255) NOT NULL,
  message LONGTEXT NOT NULL,
  html_message LONGTEXT NOT NULL,
  status SMALLINT(5) UNSIGNED DEFAULT NULL,
  priority SMALLINT(5) UNSIGNED DEFAULT NULL,
  created DATETIME(6) NOT NULL,
  last_updated DATETIME(6) NOT NULL,
  scheduled_time DATETIME(6) DEFAULT NULL,
  headers LONGTEXT DEFAULT NULL,
  context LONGTEXT DEFAULT NULL,
  template_id INT(11) DEFAULT NULL,
  backend_alias VARCHAR(64) NOT NULL,
  PRIMARY KEY (id),
  INDEX post_office_email_3acc0b7a (last_updated),
  INDEX post_office_email_74f53564 (template_id),
  INDEX post_office_email_9acb4454 (status),
  INDEX post_office_email_e2fa5388 (created),
  INDEX post_office_email_ed24d584 (scheduled_time),
  CONSTRAINT post_office_template_id_417da7da_fk_post_office_emailtemplate_id FOREIGN KEY (template_id)
    REFERENCES post_office_emailtemplate(id) ON DELETE RESTRICT ON UPDATE RESTRICT
)
ENGINE = INNODB
AUTO_INCREMENT = 1
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы todos_customer
--
CREATE TABLE todos_customer (
  user_id INT(11) NOT NULL,
  recognized SMALLINT(5) UNSIGNED NOT NULL,
  salutation VARCHAR(5) NOT NULL,
  last_access DATETIME(6) NOT NULL,
  extra LONGTEXT NOT NULL,
  number INT(10) UNSIGNED DEFAULT NULL,
  PRIMARY KEY (user_id),
  UNIQUE INDEX number (number),
  CONSTRAINT todos_customer_user_id_8b0f9ee3_fk_auth_user_id FOREIGN KEY (user_id)
    REFERENCES auth_user(id) ON DELETE RESTRICT ON UPDATE RESTRICT
)
ENGINE = INNODB
AVG_ROW_LENGTH = 16384
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы todos_datamart
--
CREATE TABLE todos_datamart (
  id INT(11) NOT NULL AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL,
  slug VARCHAR(50) NOT NULL,
  path VARCHAR(255) NOT NULL,
  created_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL,
  view_class VARCHAR(255) DEFAULT NULL,
  description LONGTEXT DEFAULT NULL,
  active TINYINT(1) NOT NULL,
  system_flags BIGINT(20) DEFAULT NULL,
  lft INT(10) UNSIGNED NOT NULL,
  rght INT(10) UNSIGNED NOT NULL,
  tree_id INT(10) UNSIGNED NOT NULL,
  level INT(10) UNSIGNED NOT NULL,
  parent_id INT(11) DEFAULT NULL,
  polymorphic_ctype_id INT(11) DEFAULT NULL,
  ordering VARCHAR(50) NOT NULL,
  `limit` INT(11) DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE INDEX path (path),
  INDEX todos_datamart_2dbcba41 (slug),
  INDEX todos_datamart_3cfbd988 (rght),
  INDEX todos_datamart_656442a0 (tree_id),
  INDEX todos_datamart_6be37982 (parent_id),
  INDEX todos_datamart_c76a5e84 (active),
  INDEX todos_datamart_c9e9a848 (level),
  INDEX todos_datamart_caf7cc51 (lft),
  CONSTRAINT todos_da_polymorphic_ctype_id_cd461564_fk_django_content_type_id FOREIGN KEY (polymorphic_ctype_id)
    REFERENCES django_content_type(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT todos_datamart_parent_id_4774ecbd_fk_todos_datamart_id FOREIGN KEY (parent_id)
    REFERENCES todos_datamart(id) ON DELETE RESTRICT ON UPDATE RESTRICT
)
ENGINE = INNODB
AUTO_INCREMENT = 4
AVG_ROW_LENGTH = 5461
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы todos_notification
--
CREATE TABLE todos_notification (
  id INT(11) NOT NULL AUTO_INCREMENT,
  name VARCHAR(50) NOT NULL,
  transition_target VARCHAR(50) NOT NULL,
  mail_to INT(10) UNSIGNED DEFAULT NULL,
  mail_template_id INT(11) NOT NULL,
  PRIMARY KEY (id),
  CONSTRAINT todos__mail_template_id_ededeeec_fk_post_office_emailtemplate_id FOREIGN KEY (mail_template_id)
    REFERENCES post_office_emailtemplate(id) ON DELETE RESTRICT ON UPDATE RESTRICT
)
ENGINE = INNODB
AUTO_INCREMENT = 1
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы todos_todo
--
CREATE TABLE todos_todo (
  id INT(11) NOT NULL AUTO_INCREMENT,
  created_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL,
  active TINYINT(1) NOT NULL,
  name VARCHAR(255) NOT NULL,
  marked TINYINT(1) NOT NULL,
  priority SMALLINT(5) UNSIGNED DEFAULT NULL,
  direction SMALLINT(5) UNSIGNED DEFAULT NULL,
  description LONGTEXT DEFAULT NULL,
  `order` INT(10) UNSIGNED NOT NULL,
  polymorphic_ctype_id INT(11) DEFAULT NULL,
  PRIMARY KEY (id),
  INDEX todos_todo_70a17ffa (`order`),
  CONSTRAINT todos_to_polymorphic_ctype_id_df409da2_fk_django_content_type_id FOREIGN KEY (polymorphic_ctype_id)
    REFERENCES django_content_type(id) ON DELETE RESTRICT ON UPDATE RESTRICT
)
ENGINE = INNODB
AUTO_INCREMENT = 22
AVG_ROW_LENGTH = 2340
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы auth_group_permissions
--
CREATE TABLE auth_group_permissions (
  id INT(11) NOT NULL AUTO_INCREMENT,
  group_id INT(11) NOT NULL,
  permission_id INT(11) NOT NULL,
  PRIMARY KEY (id),
  INDEX auth_group_permissions_0e939a4f (group_id),
  INDEX auth_group_permissions_8373b171 (permission_id),
  UNIQUE INDEX auth_group_permissions_group_id_0cd325b0_uniq (group_id, permission_id),
  CONSTRAINT auth_group_permissi_permission_id_84c5c92e_fk_auth_permission_id FOREIGN KEY (permission_id)
    REFERENCES auth_permission(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT auth_group_permissions_group_id_b120cbf9_fk_auth_group_id FOREIGN KEY (group_id)
    REFERENCES auth_group(id) ON DELETE RESTRICT ON UPDATE RESTRICT
)
ENGINE = INNODB
AUTO_INCREMENT = 1
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы auth_user_user_permissions
--
CREATE TABLE auth_user_user_permissions (
  id INT(11) NOT NULL AUTO_INCREMENT,
  user_id INT(11) NOT NULL,
  permission_id INT(11) NOT NULL,
  PRIMARY KEY (id),
  INDEX auth_user_user_permissions_8373b171 (permission_id),
  INDEX auth_user_user_permissions_e8701ad4 (user_id),
  UNIQUE INDEX auth_user_user_permissions_user_id_14a6b632_uniq (user_id, permission_id),
  CONSTRAINT auth_user_user_perm_permission_id_1fbb5f2c_fk_auth_permission_id FOREIGN KEY (permission_id)
    REFERENCES auth_permission(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id FOREIGN KEY (user_id)
    REFERENCES auth_user(id) ON DELETE RESTRICT ON UPDATE RESTRICT
)
ENGINE = INNODB
AUTO_INCREMENT = 1
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы easy_thumbnails_thumbnaildimensions
--
CREATE TABLE easy_thumbnails_thumbnaildimensions (
  id INT(11) NOT NULL AUTO_INCREMENT,
  thumbnail_id INT(11) NOT NULL,
  width INT(10) UNSIGNED DEFAULT NULL,
  height INT(10) UNSIGNED DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE INDEX thumbnail_id (thumbnail_id),
  CONSTRAINT easy_thumb_thumbnail_id_c3a0c549_fk_easy_thumbnails_thumbnail_id FOREIGN KEY (thumbnail_id)
    REFERENCES easy_thumbnails_thumbnail(id) ON DELETE RESTRICT ON UPDATE RESTRICT
)
ENGINE = INNODB
AUTO_INCREMENT = 1
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы filer_file
--
CREATE TABLE filer_file (
  id INT(11) NOT NULL AUTO_INCREMENT,
  file VARCHAR(255) DEFAULT NULL,
  _file_size INT(11) DEFAULT NULL,
  sha1 VARCHAR(40) NOT NULL,
  has_all_mandatory_data TINYINT(1) NOT NULL,
  original_filename VARCHAR(255) DEFAULT NULL,
  name VARCHAR(255) NOT NULL,
  description LONGTEXT DEFAULT NULL,
  uploaded_at DATETIME(6) NOT NULL,
  modified_at DATETIME(6) NOT NULL,
  is_public TINYINT(1) NOT NULL,
  folder_id INT(11) DEFAULT NULL,
  owner_id INT(11) DEFAULT NULL,
  polymorphic_ctype_id INT(11) DEFAULT NULL,
  PRIMARY KEY (id),
  INDEX filer_file_5e7b1936 (owner_id),
  INDEX filer_file_a8a44dbb (folder_id),
  INDEX filer_file_d3e32c49 (polymorphic_ctype_id),
  CONSTRAINT filer_fi_polymorphic_ctype_id_f44903c1_fk_django_content_type_id FOREIGN KEY (polymorphic_ctype_id)
    REFERENCES django_content_type(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT filer_file_folder_id_af803bbb_fk_filer_folder_id FOREIGN KEY (folder_id)
    REFERENCES filer_folder(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT filer_file_owner_id_b9e32671_fk_auth_user_id FOREIGN KEY (owner_id)
    REFERENCES auth_user(id) ON DELETE RESTRICT ON UPDATE RESTRICT
)
ENGINE = INNODB
AUTO_INCREMENT = 1
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы filer_folderpermission
--
CREATE TABLE filer_folderpermission (
  id INT(11) NOT NULL AUTO_INCREMENT,
  type SMALLINT(6) NOT NULL,
  everybody TINYINT(1) NOT NULL,
  can_edit SMALLINT(6) DEFAULT NULL,
  can_read SMALLINT(6) DEFAULT NULL,
  can_add_children SMALLINT(6) DEFAULT NULL,
  folder_id INT(11) DEFAULT NULL,
  group_id INT(11) DEFAULT NULL,
  user_id INT(11) DEFAULT NULL,
  PRIMARY KEY (id),
  CONSTRAINT filer_folderpermission_folder_id_5d02f1da_fk_filer_folder_id FOREIGN KEY (folder_id)
    REFERENCES filer_folder(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT filer_folderpermission_group_id_8901bafa_fk_auth_group_id FOREIGN KEY (group_id)
    REFERENCES auth_group(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT filer_folderpermission_user_id_7673d4b6_fk_auth_user_id FOREIGN KEY (user_id)
    REFERENCES auth_user(id) ON DELETE RESTRICT ON UPDATE RESTRICT
)
ENGINE = INNODB
AUTO_INCREMENT = 1
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы post_office_attachment_emails
--
CREATE TABLE post_office_attachment_emails (
  id INT(11) NOT NULL AUTO_INCREMENT,
  attachment_id INT(11) NOT NULL,
  email_id INT(11) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE INDEX post_office_attachment_emails_attachment_id_8e046917_uniq (attachment_id, email_id),
  CONSTRAINT post_office__attachment_id_6136fd9a_fk_post_office_attachment_id FOREIGN KEY (attachment_id)
    REFERENCES post_office_attachment(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT post_office_attachment_email_id_96875fd9_fk_post_office_email_id FOREIGN KEY (email_id)
    REFERENCES post_office_email(id) ON DELETE RESTRICT ON UPDATE RESTRICT
)
ENGINE = INNODB
AUTO_INCREMENT = 1
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы post_office_log
--
CREATE TABLE post_office_log (
  id INT(11) NOT NULL AUTO_INCREMENT,
  date DATETIME(6) NOT NULL,
  status SMALLINT(5) UNSIGNED NOT NULL,
  exception_type VARCHAR(255) NOT NULL,
  message LONGTEXT NOT NULL,
  email_id INT(11) NOT NULL,
  PRIMARY KEY (id),
  CONSTRAINT post_office_log_email_id_d42c8808_fk_post_office_email_id FOREIGN KEY (email_id)
    REFERENCES post_office_email(id) ON DELETE RESTRICT ON UPDATE RESTRICT
)
ENGINE = INNODB
AUTO_INCREMENT = 1
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы todos_additionalentitycharacteristicormark
--
CREATE TABLE todos_additionalentitycharacteristicormark (
  id INT(11) NOT NULL AUTO_INCREMENT,
  value VARCHAR(255) NOT NULL,
  view_class VARCHAR(255) DEFAULT NULL,
  entity_id INT(11) NOT NULL,
  term_id INT(11) NOT NULL,
  PRIMARY KEY (id),
  INDEX todos_additionalentitycharacteristicormark_ba3248a2 (term_id),
  INDEX todos_additionalentitycharacteristicormark_dffc4713 (entity_id),
  CONSTRAINT todos_additionalentitycharac_entity_id_a794476d_fk_todos_todo_id FOREIGN KEY (entity_id)
    REFERENCES todos_todo(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT todos_additionalentitycharacte_term_id_5dd631fe_fk_todos_term_id FOREIGN KEY (term_id)
    REFERENCES todos_term(id) ON DELETE RESTRICT ON UPDATE RESTRICT
)
ENGINE = INNODB
AUTO_INCREMENT = 1
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы todos_datamart_terms
--
CREATE TABLE todos_datamart_terms (
  id INT(11) NOT NULL AUTO_INCREMENT,
  datamart_id INT(11) NOT NULL,
  term_id INT(11) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE INDEX todos_datamart_terms_datamart_id_4c231ab3_uniq (datamart_id, term_id),
  CONSTRAINT todos_datamart_terms_datamart_id_7ca7f47b_fk_todos_datamart_id FOREIGN KEY (datamart_id)
    REFERENCES todos_datamart(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT todos_datamart_terms_term_id_8ed02640_fk_todos_term_id FOREIGN KEY (term_id)
    REFERENCES todos_term(id) ON DELETE RESTRICT ON UPDATE RESTRICT
)
ENGINE = INNODB
AUTO_INCREMENT = 47
AVG_ROW_LENGTH = 910
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы todos_datamartrelation
--
CREATE TABLE todos_datamartrelation (
  id INT(11) NOT NULL AUTO_INCREMENT,
  direction VARCHAR(1) NOT NULL,
  data_mart_id INT(11) NOT NULL,
  term_id INT(11) NOT NULL,
  PRIMARY KEY (id),
  INDEX todos_datamartrelation_2536d9e9 (data_mart_id),
  INDEX todos_datamartrelation_ba3248a2 (term_id),
  UNIQUE INDEX todos_datamartrelation_data_mart_id_33c77f28_uniq (data_mart_id, term_id),
  CONSTRAINT todos_datamartrelatio_data_mart_id_bf7ef36d_fk_todos_datamart_id FOREIGN KEY (data_mart_id)
    REFERENCES todos_datamart(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT todos_datamartrelation_term_id_5a4aa9bb_fk_todos_term_id FOREIGN KEY (term_id)
    REFERENCES todos_term(id) ON DELETE RESTRICT ON UPDATE RESTRICT
)
ENGINE = INNODB
AUTO_INCREMENT = 1
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы todos_entityrelateddatamart
--
CREATE TABLE todos_entityrelateddatamart (
  id INT(11) NOT NULL AUTO_INCREMENT,
  data_mart_id INT(11) NOT NULL,
  entity_id INT(11) NOT NULL,
  PRIMARY KEY (id),
  INDEX todos_entityrelateddatamart_2536d9e9 (data_mart_id),
  INDEX todos_entityrelateddatamart_dffc4713 (entity_id),
  CONSTRAINT todos_entityrelatedda_data_mart_id_24d5419c_fk_todos_datamart_id FOREIGN KEY (data_mart_id)
    REFERENCES todos_datamart(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT todos_entityrelateddatamart_entity_id_48f6ae78_fk_todos_todo_id FOREIGN KEY (entity_id)
    REFERENCES todos_todo(id) ON DELETE RESTRICT ON UPDATE RESTRICT
)
ENGINE = INNODB
AUTO_INCREMENT = 1
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы todos_entityrelation
--
CREATE TABLE todos_entityrelation (
  id INT(11) NOT NULL AUTO_INCREMENT,
  from_entity_id INT(11) NOT NULL,
  term_id INT(11) NOT NULL,
  to_entity_id INT(11) NOT NULL,
  PRIMARY KEY (id),
  INDEX todos_entityrelation_95c8745a (to_entity_id),
  INDEX todos_entityrelation_9f55278f (from_entity_id),
  INDEX todos_entityrelation_ba3248a2 (term_id),
  UNIQUE INDEX todos_entityrelation_term_id_d12e2dd4_uniq (term_id, from_entity_id, to_entity_id),
  CONSTRAINT todos_entityrelation_from_entity_id_a4a66dc5_fk_todos_todo_id FOREIGN KEY (from_entity_id)
    REFERENCES todos_todo(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT todos_entityrelation_term_id_ad099a31_fk_todos_term_id FOREIGN KEY (term_id)
    REFERENCES todos_term(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT todos_entityrelation_to_entity_id_65f38203_fk_todos_todo_id FOREIGN KEY (to_entity_id)
    REFERENCES todos_todo(id) ON DELETE RESTRICT ON UPDATE RESTRICT
)
ENGINE = INNODB
AUTO_INCREMENT = 2
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы todos_todo_terms
--
CREATE TABLE todos_todo_terms (
  id INT(11) NOT NULL AUTO_INCREMENT,
  todo_id INT(11) NOT NULL,
  term_id INT(11) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE INDEX todos_todo_terms_todo_id_39f0311e_uniq (todo_id, term_id),
  CONSTRAINT todos_todo_terms_term_id_dae83918_fk_todos_term_id FOREIGN KEY (term_id)
    REFERENCES todos_term(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT todos_todo_terms_todo_id_352dd1df_fk_todos_todo_id FOREIGN KEY (todo_id)
    REFERENCES todos_todo(id) ON DELETE RESTRICT ON UPDATE RESTRICT
)
ENGINE = INNODB
AUTO_INCREMENT = 45
AVG_ROW_LENGTH = 655
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы filer_clipboarditem
--
CREATE TABLE filer_clipboarditem (
  id INT(11) NOT NULL AUTO_INCREMENT,
  clipboard_id INT(11) NOT NULL,
  file_id INT(11) NOT NULL,
  PRIMARY KEY (id),
  INDEX filer_clipboarditem_814552b9 (file_id),
  CONSTRAINT filer_clipboarditem_clipboard_id_7a76518b_fk_filer_clipboard_id FOREIGN KEY (clipboard_id)
    REFERENCES filer_clipboard(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT filer_clipboarditem_file_id_06196f80_fk_filer_file_id FOREIGN KEY (file_id)
    REFERENCES filer_file(id) ON DELETE RESTRICT ON UPDATE RESTRICT
)
ENGINE = INNODB
AUTO_INCREMENT = 1
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы filer_image
--
CREATE TABLE filer_image (
  file_ptr_id INT(11) NOT NULL,
  _height INT(11) DEFAULT NULL,
  _width INT(11) DEFAULT NULL,
  date_taken DATETIME(6) DEFAULT NULL,
  default_alt_text VARCHAR(255) DEFAULT NULL,
  default_caption VARCHAR(255) DEFAULT NULL,
  author VARCHAR(255) DEFAULT NULL,
  must_always_publish_author_credit TINYINT(1) NOT NULL,
  must_always_publish_copyright TINYINT(1) NOT NULL,
  subject_location VARCHAR(64) NOT NULL,
  PRIMARY KEY (file_ptr_id),
  CONSTRAINT filer_image_file_ptr_id_3e21d4f0_fk_filer_file_id FOREIGN KEY (file_ptr_id)
    REFERENCES filer_file(id) ON DELETE RESTRICT ON UPDATE RESTRICT
)
ENGINE = INNODB
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы todos_notificationattachment
--
CREATE TABLE todos_notificationattachment (
  id INT(11) NOT NULL AUTO_INCREMENT,
  attachment_id INT(11) DEFAULT NULL,
  notification_id INT(11) NOT NULL,
  PRIMARY KEY (id),
  INDEX todos_notificationattachment_07ba63f5 (attachment_id),
  CONSTRAINT todos_notifica_notification_id_53f91688_fk_todos_notification_id FOREIGN KEY (notification_id)
    REFERENCES todos_notification(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT todos_notificationattach_attachment_id_08694251_fk_filer_file_id FOREIGN KEY (attachment_id)
    REFERENCES filer_file(id) ON DELETE RESTRICT ON UPDATE RESTRICT
)
ENGINE = INNODB
AUTO_INCREMENT = 1
CHARACTER SET utf8
COLLATE utf8_general_ci;

--
-- Описание для таблицы todos_entityimage
--
CREATE TABLE todos_entityimage (
  id INT(11) NOT NULL AUTO_INCREMENT,
  `order` SMALLINT(6) NOT NULL,
  entity_id INT(11) NOT NULL,
  image_id INT(11) NOT NULL,
  PRIMARY KEY (id),
  INDEX todos_entityimage_f33175e6 (image_id),
  CONSTRAINT todos_entityimage_entity_id_5fd78980_fk_todos_todo_id FOREIGN KEY (entity_id)
    REFERENCES todos_todo(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT todos_entityimage_image_id_62b0a296_fk_filer_image_file_ptr_id FOREIGN KEY (image_id)
    REFERENCES filer_image(file_ptr_id) ON DELETE RESTRICT ON UPDATE RESTRICT
)
ENGINE = INNODB
AUTO_INCREMENT = 1
CHARACTER SET utf8
COLLATE utf8_general_ci;

-- 
-- Вывод данных для таблицы auth_group
--

-- Таблица edw_todos_db.auth_group не содержит данных

-- 
-- Вывод данных для таблицы auth_user
--
INSERT INTO auth_user VALUES
(2, 'pbkdf2_sha256$24000$j8BZRWW9cTmJ$lAAgSG+ElFUQAyLfpdPXFkQ3qRzwYXY2TJ/XTiWYf7o=', '2016-09-07 10:42:50.024774', 1, 'rufus', '', '', 'rebus_vs@mail.ru', 1, 1, '2016-09-05 11:46:49.287673'),
(3, 'pbkdf2_sha256$24000$3ToDWlFvgMMx$AyDswC9ye4Bbkjlne3Q64SXadjALENj/72vl15Qe+So=', '2016-11-16 16:09:33.24106', 1, 'root', '', '', 'rebus.vs@gmail.com', 1, 1, '2016-09-05 11:49:20.436408');

-- 
-- Вывод данных для таблицы django_content_type
--
INSERT INTO django_content_type VALUES
(7, 'admin', 'logentry'),
(2, 'auth', 'group'),
(1, 'auth', 'permission'),
(8, 'authtoken', 'token'),
(4, 'contenttypes', 'contenttype'),
(20, 'easy_thumbnails', 'source'),
(21, 'easy_thumbnails', 'thumbnail'),
(22, 'easy_thumbnails', 'thumbnaildimensions'),
(31, 'edw', 'email'),
(3, 'email_auth', 'user'),
(16, 'filer', 'clipboard'),
(17, 'filer', 'clipboarditem'),
(15, 'filer', 'file'),
(13, 'filer', 'folder'),
(14, 'filer', 'folderpermission'),
(18, 'filer', 'image'),
(19, 'filer', 'thumbnailoption'),
(12, 'post_office', 'attachment'),
(9, 'post_office', 'email'),
(11, 'post_office', 'emailtemplate'),
(10, 'post_office', 'log'),
(5, 'sessions', 'session'),
(6, 'sites', 'site'),
(26, 'todos', 'additionalentitycharacteristicormark'),
(23, 'todos', 'customer'),
(28, 'todos', 'customerproxy'),
(25, 'todos', 'datamart'),
(35, 'todos', 'datamartrelation'),
(30, 'todos', 'entityimage'),
(34, 'todos', 'entityrelateddatamart'),
(29, 'todos', 'entityrelation'),
(32, 'todos', 'notification'),
(33, 'todos', 'notificationattachment'),
(24, 'todos', 'term'),
(27, 'todos', 'todo');

-- 
-- Вывод данных для таблицы django_migrations
--
INSERT INTO django_migrations VALUES
(1, 'contenttypes', '0001_initial', '2016-09-01 22:15:21.425933'),
(2, 'auth', '0001_initial', '2016-09-01 22:15:22.038747'),
(3, 'email_auth', '0001_initial', '2016-09-01 22:15:23.45599'),
(4, 'admin', '0001_initial', '2016-09-01 22:15:23.905764'),
(5, 'admin', '0002_logentry_remove_auto_add', '2016-09-01 22:15:23.971578'),
(6, 'contenttypes', '0002_remove_content_type_name', '2016-09-01 22:15:24.205373'),
(7, 'auth', '0002_alter_permission_name_max_length', '2016-09-01 22:15:24.298039'),
(8, 'auth', '0003_alter_user_email_max_length', '2016-09-01 22:15:24.362284'),
(9, 'auth', '0004_alter_user_username_opts', '2016-09-01 22:15:24.382569'),
(10, 'auth', '0005_alter_user_last_login_null', '2016-09-01 22:15:24.404925'),
(11, 'auth', '0006_require_contenttypes_0002', '2016-09-01 22:15:24.411183'),
(12, 'auth', '0007_alter_validators_add_error_messages', '2016-09-01 22:15:24.43146'),
(13, 'authtoken', '0001_initial', '2016-09-01 22:15:24.682599'),
(14, 'authtoken', '0002_auto_20160226_1747', '2016-09-01 22:15:24.824818'),
(15, 'easy_thumbnails', '0001_initial', '2016-09-01 22:15:25.185423'),
(16, 'easy_thumbnails', '0002_thumbnaildimensions', '2016-09-01 22:15:25.297529'),
(17, 'email_auth', '0002_auto_20160327_1119', '2016-09-01 22:15:25.317087'),
(18, 'filer', '0001_initial', '2016-09-01 22:15:27.915742'),
(19, 'filer', '0002_auto_20150606_2003', '2016-09-01 22:15:28.160935'),
(20, 'filer', '0003_thumbnailoption', '2016-09-01 22:15:28.264532'),
(21, 'filer', '0004_auto_20160328_1434', '2016-09-01 22:15:28.362882'),
(22, 'filer', '0005_auto_20160623_1425', '2016-09-01 22:15:28.981536'),
(23, 'filer', '0006_auto_20160623_1627', '2016-09-01 22:15:29.188105'),
(24, 'post_office', '0001_initial', '2016-09-01 22:15:29.954342'),
(25, 'post_office', '0002_add_i18n_and_backend_alias', '2016-09-01 22:15:30.523552'),
(26, 'post_office', '0003_auto_20160831_1555', '2016-09-01 22:15:30.544406'),
(27, 'sessions', '0001_initial', '2016-09-01 22:15:30.622405'),
(28, 'sites', '0001_initial', '2016-09-01 22:15:30.670716'),
(29, 'sites', '0002_alter_domain_unique', '2016-09-01 22:15:30.711552'),
(30, 'todos', '0001_initial', '2016-09-01 22:15:32.882867'),
(31, 'todos', '0002_remove_todo_slug', '2016-09-02 08:23:00.506776'),
(32, 'todos', '0003_auto_20160913_1114', '2016-09-14 07:41:02.824285'),
(33, 'todos', '0004_entityimage', '2016-09-14 07:41:04.768349'),
(34, 'edw', '0001_initial', '2016-09-23 13:28:09.029652'),
(35, 'todos', '0005_auto_20160923_1628', '2016-09-23 13:28:10.807334'),
(36, 'edw', '0002_delete_email', '2016-10-06 13:11:53.213634'),
(37, 'todos', '0006_auto_20161006_1611', '2016-10-06 13:11:54.186523'),
(38, 'todos', '0007_auto_20161017_1356', '2016-10-17 10:56:49.537821'),
(39, 'todos', '0008_auto_20161103_1424', '2016-11-03 11:25:11.223246'),
(40, 'todos', '0009_datamart_limit', '2016-11-24 14:27:40.137321');

-- 
-- Вывод данных для таблицы django_session
--
INSERT INTO django_session VALUES
('0fiiqjx59xp5zxy2zxytmdrfkiubs5ws', 'MDFjZGFkZGUwMmIyYTU2YmUxMWY3ZjQwMzhmNzcxMTlhNTdiYTdjYzp7Il9hdXRoX3VzZXJfaGFzaCI6IjlkMGM5NmIwNWQzZGYwODRhZjNmODNmNTkzYmIxZGM4NWEyNDMyODIiLCJfYXV0aF91c2VyX2JhY2tlbmQiOiJkamFuZ28uY29udHJpYi5hdXRoLmJhY2tlbmRzLk1vZGVsQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOiIzIn0=', '2016-11-10 22:03:08.468971'),
('25yfbhblxla5c7g6yoe4z1d63760nuzf', 'MDFjZGFkZGUwMmIyYTU2YmUxMWY3ZjQwMzhmNzcxMTlhNTdiYTdjYzp7Il9hdXRoX3VzZXJfaGFzaCI6IjlkMGM5NmIwNWQzZGYwODRhZjNmODNmNTkzYmIxZGM4NWEyNDMyODIiLCJfYXV0aF91c2VyX2JhY2tlbmQiOiJkamFuZ28uY29udHJpYi5hdXRoLmJhY2tlbmRzLk1vZGVsQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOiIzIn0=', '2016-11-29 11:27:10.689821'),
('27jagi5qzhooehikacrqpqwtim4c7xps', 'MWMxOTc5NTlmMDA4YzRjMWUwODNkZGNhZWNlODI5MTY2YjY0OGQ4Yjp7Il9hdXRoX3VzZXJfaGFzaCI6IjJjNDhmN2ZiYWY3MDRmOTMxZDg1ZDI3NWVmYTU1Mzc5ZTk3MTk1ZGUiLCJfYXV0aF91c2VyX2lkIjoiMSIsIl9hdXRoX3VzZXJfYmFja2VuZCI6ImRqYW5nby5jb250cmliLmF1dGguYmFja2VuZHMuTW9kZWxCYWNrZW5kIn0=', '2016-09-16 12:05:15.518119'),
('buz9ekli1ancfjh2pndoxt5g06hwzlyc', 'OGFjNjIyN2YzZTViNDdhNGJjMGJiOWE3OTlkNjM2MmVmYjcyOGNkMjp7Il9hdXRoX3VzZXJfaGFzaCI6IjJjNDhmN2ZiYWY3MDRmOTMxZDg1ZDI3NWVmYTU1Mzc5ZTk3MTk1ZGUiLCJfYXV0aF91c2VyX2JhY2tlbmQiOiJkamFuZ28uY29udHJpYi5hdXRoLmJhY2tlbmRzLk1vZGVsQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOiIxIn0=', '2016-09-15 22:40:13.198928'),
('gjyi342j2zvr44dj5esr0ve5ev8ihrl9', 'MDFjZGFkZGUwMmIyYTU2YmUxMWY3ZjQwMzhmNzcxMTlhNTdiYTdjYzp7Il9hdXRoX3VzZXJfaGFzaCI6IjlkMGM5NmIwNWQzZGYwODRhZjNmODNmNTkzYmIxZGM4NWEyNDMyODIiLCJfYXV0aF91c2VyX2JhY2tlbmQiOiJkamFuZ28uY29udHJpYi5hdXRoLmJhY2tlbmRzLk1vZGVsQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOiIzIn0=', '2016-11-25 12:07:28.587611'),
('ju0m8pxffc8061jff38vbjz9h98ac80b', 'MDFjZGFkZGUwMmIyYTU2YmUxMWY3ZjQwMzhmNzcxMTlhNTdiYTdjYzp7Il9hdXRoX3VzZXJfaGFzaCI6IjlkMGM5NmIwNWQzZGYwODRhZjNmODNmNTkzYmIxZGM4NWEyNDMyODIiLCJfYXV0aF91c2VyX2JhY2tlbmQiOiJkamFuZ28uY29udHJpYi5hdXRoLmJhY2tlbmRzLk1vZGVsQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOiIzIn0=', '2016-10-07 13:28:48.81349'),
('k1oy8fqtcd0hee5mzxopxjs8lesjgmck', 'MDFjZGFkZGUwMmIyYTU2YmUxMWY3ZjQwMzhmNzcxMTlhNTdiYTdjYzp7Il9hdXRoX3VzZXJfaGFzaCI6IjlkMGM5NmIwNWQzZGYwODRhZjNmODNmNTkzYmIxZGM4NWEyNDMyODIiLCJfYXV0aF91c2VyX2JhY2tlbmQiOiJkamFuZ28uY29udHJpYi5hdXRoLmJhY2tlbmRzLk1vZGVsQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOiIzIn0=', '2016-09-29 15:15:19.891232'),
('nddsbv1tcuhbd8j628h326vb2vy3dvq1', 'MDFjZGFkZGUwMmIyYTU2YmUxMWY3ZjQwMzhmNzcxMTlhNTdiYTdjYzp7Il9hdXRoX3VzZXJfaGFzaCI6IjlkMGM5NmIwNWQzZGYwODRhZjNmODNmNTkzYmIxZGM4NWEyNDMyODIiLCJfYXV0aF91c2VyX2JhY2tlbmQiOiJkamFuZ28uY29udHJpYi5hdXRoLmJhY2tlbmRzLk1vZGVsQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOiIzIn0=', '2016-10-24 19:53:24.751095'),
('r2oeh1h22sngytlgwtyw4uwvbnobd38x', 'MDFjZGFkZGUwMmIyYTU2YmUxMWY3ZjQwMzhmNzcxMTlhNTdiYTdjYzp7Il9hdXRoX3VzZXJfaGFzaCI6IjlkMGM5NmIwNWQzZGYwODRhZjNmODNmNTkzYmIxZGM4NWEyNDMyODIiLCJfYXV0aF91c2VyX2JhY2tlbmQiOiJkamFuZ28uY29udHJpYi5hdXRoLmJhY2tlbmRzLk1vZGVsQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOiIzIn0=', '2016-09-29 16:10:07.999228'),
('rplvn0qws45s3arcrn4xkb26qju8phv1', 'MDFjZGFkZGUwMmIyYTU2YmUxMWY3ZjQwMzhmNzcxMTlhNTdiYTdjYzp7Il9hdXRoX3VzZXJfaGFzaCI6IjlkMGM5NmIwNWQzZGYwODRhZjNmODNmNTkzYmIxZGM4NWEyNDMyODIiLCJfYXV0aF91c2VyX2JhY2tlbmQiOiJkamFuZ28uY29udHJpYi5hdXRoLmJhY2tlbmRzLk1vZGVsQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOiIzIn0=', '2016-11-30 16:09:33.252408'),
('sfx9ukrnsu1r3fyct63zm27ymqfrodm9', 'MWMxOTc5NTlmMDA4YzRjMWUwODNkZGNhZWNlODI5MTY2YjY0OGQ4Yjp7Il9hdXRoX3VzZXJfaGFzaCI6IjJjNDhmN2ZiYWY3MDRmOTMxZDg1ZDI3NWVmYTU1Mzc5ZTk3MTk1ZGUiLCJfYXV0aF91c2VyX2lkIjoiMSIsIl9hdXRoX3VzZXJfYmFja2VuZCI6ImRqYW5nby5jb250cmliLmF1dGguYmFja2VuZHMuTW9kZWxCYWNrZW5kIn0=', '2016-09-15 23:14:14.483252'),
('svr5ydvale0mcqpi5ocj8ruf32or0w0t', 'MDFjZGFkZGUwMmIyYTU2YmUxMWY3ZjQwMzhmNzcxMTlhNTdiYTdjYzp7Il9hdXRoX3VzZXJfaGFzaCI6IjlkMGM5NmIwNWQzZGYwODRhZjNmODNmNTkzYmIxZGM4NWEyNDMyODIiLCJfYXV0aF91c2VyX2JhY2tlbmQiOiJkamFuZ28uY29udHJpYi5hdXRoLmJhY2tlbmRzLk1vZGVsQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOiIzIn0=', '2016-11-15 14:24:40.829167'),
('ue5q6ne5pofl4l493i5zx9mg7kvnpw9q', 'OWUzYmYxNDdmZWM2MDEwNDczZjAyYTliNTFiNTE2NTk3YTU1ODZkYzp7Il9hdXRoX3VzZXJfaGFzaCI6IjlkMGM5NmIwNWQzZGYwODRhZjNmODNmNTkzYmIxZGM4NWEyNDMyODIiLCJfYXV0aF91c2VyX2lkIjoiMyIsIl9hdXRoX3VzZXJfYmFja2VuZCI6ImRqYW5nby5jb250cmliLmF1dGguYmFja2VuZHMuTW9kZWxCYWNrZW5kIn0=', '2016-09-21 10:44:15.762082'),
('v15ar2uqd26xtzpdmcbwlym7xsrq474n', 'OWUzYmYxNDdmZWM2MDEwNDczZjAyYTliNTFiNTE2NTk3YTU1ODZkYzp7Il9hdXRoX3VzZXJfaGFzaCI6IjlkMGM5NmIwNWQzZGYwODRhZjNmODNmNTkzYmIxZGM4NWEyNDMyODIiLCJfYXV0aF91c2VyX2lkIjoiMyIsIl9hdXRoX3VzZXJfYmFja2VuZCI6ImRqYW5nby5jb250cmliLmF1dGguYmFja2VuZHMuTW9kZWxCYWNrZW5kIn0=', '2016-09-21 10:51:31.547616'),
('xtww9h3lt8kk346a7davw3l8jxxfe68c', 'MDFjZGFkZGUwMmIyYTU2YmUxMWY3ZjQwMzhmNzcxMTlhNTdiYTdjYzp7Il9hdXRoX3VzZXJfaGFzaCI6IjlkMGM5NmIwNWQzZGYwODRhZjNmODNmNTkzYmIxZGM4NWEyNDMyODIiLCJfYXV0aF91c2VyX2JhY2tlbmQiOiJkamFuZ28uY29udHJpYi5hdXRoLmJhY2tlbmRzLk1vZGVsQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOiIzIn0=', '2016-10-31 14:29:57.704674'),
('yqpqfn1t6tivot45mczv05lux8iayyd5', 'ODAzY2Q3NTg4ZDcxZTNkMThkMzFiZTI5OGJlODFiZTJhYjRhYWJjNzp7Il9hdXRoX3VzZXJfaGFzaCI6IjlkMGM5NmIwNWQzZGYwODRhZjNmODNmNTkzYmIxZGM4NWEyNDMyODIiLCJmaWxlcl9sYXN0X2ZvbGRlcl9pZCI6bnVsbCwiX2F1dGhfdXNlcl9pZCI6IjMiLCJfYXV0aF91c2VyX2JhY2tlbmQiOiJkamFuZ28uY29udHJpYi5hdXRoLmJhY2tlbmRzLk1vZGVsQmFja2VuZCJ9', '2016-11-17 11:56:42.423208'),
('ytozfc2ylwakiuvqo4gt5yw7k076vehu', 'ZDQ1MGNjNjdiZTc0ZjRhNGQ2NTllNjYwYWVlYTJmY2RiZTNjNDhmODp7Il9hdXRoX3VzZXJfaGFzaCI6ImQyNzZjOWI1OThhM2RlNGM0NjIwOGY3MjgwMDRmNjZlNmFlOGU2M2EiLCJfYXV0aF91c2VyX2lkIjoiMyIsIl9hdXRoX3VzZXJfYmFja2VuZCI6ImRqYW5nby5jb250cmliLmF1dGguYmFja2VuZHMuTW9kZWxCYWNrZW5kIn0=', '2016-09-20 19:11:20.867715');

-- 
-- Вывод данных для таблицы django_site
--
INSERT INTO django_site VALUES
(1, 'example.com', 'example.com');

-- 
-- Вывод данных для таблицы easy_thumbnails_source
--

-- Таблица edw_todos_db.easy_thumbnails_source не содержит данных

-- 
-- Вывод данных для таблицы filer_thumbnailoption
--

-- Таблица edw_todos_db.filer_thumbnailoption не содержит данных

-- 
-- Вывод данных для таблицы post_office_attachment
--

-- Таблица edw_todos_db.post_office_attachment не содержит данных

-- 
-- Вывод данных для таблицы post_office_emailtemplate
--

-- Таблица edw_todos_db.post_office_emailtemplate не содержит данных

-- 
-- Вывод данных для таблицы todos_term
--
INSERT INTO todos_term VALUES
(1, 'Вид', 'vid', 'vid', 20, 1, 30, '2016-09-01 09:48:31.866896', '2016-11-11 13:04:55.817515', NULL, 'test___', 1, 0, 1, 6, 1, 0, NULL),
(2, 'Рабочее', 'rabochee', 'vid/rabochee', 30, 0, 10, '2016-09-01 09:49:07.287624', '2016-09-01 09:55:15.498308', NULL, '', 1, 0, 2, 3, 1, 1, 1),
(3, 'Личное', 'lichnoe', 'vid/lichnoe', 30, 0, 10, '2016-09-01 09:49:14.267012', '2016-09-01 09:55:21.978142', NULL, '', 1, 0, 4, 5, 1, 1, 1),
(4, 'Направление', 'napravlenie', 'napravlenie', 10, 1, 10, '2016-09-01 09:49:30.998872', '2016-09-01 22:50:15.716412', 'direction', '', 1, 0, 1, 22, 3, 0, NULL),
(5, 'Здоровье', 'zdorove', 'napravlenie/zdorove', 10, 0, 10, '2016-09-01 09:50:11.904556', '2016-09-01 09:53:51.103124', 'health', '', 1, 0, 2, 3, 3, 1, 4),
(6, 'Семья', 'semya', 'napravlenie/semya', 10, 0, 10, '2016-09-01 09:50:28.052175', '2016-09-01 09:54:05.129704', 'family', '', 1, 0, 4, 5, 3, 1, 4),
(7, 'Финансы', 'finansy', 'napravlenie/finansy', 30, 0, 30, '2016-09-01 09:50:56.260197', '2016-11-11 12:53:32.474093', 'finance', 'Департамент городского хозяйства администрации города Белгорода доводит до сведения горожан официальное сообщение о проведении отбора дворовых территорий многоквартирных домов для формирования адресного перечня дворовых территорий на проведение работ по комплексному благоустройству дворовых территорий в городском округе «Город Белгород».', 1, 0, 6, 19, 3, 1, 4),
(8, 'Хобби', 'hobbi', 'napravlenie/hobbi', 10, 0, 10, '2016-09-01 09:51:09.908891', '2016-09-01 09:54:20.580387', 'hobby', '', 1, 0, 20, 21, 3, 1, 4),
(9, 'Приоритет', 'prioritet', 'prioritet', 20, 3, 10, '2016-09-01 09:51:33.267616', '2016-09-01 09:52:52.639264', 'priority', '', 1, 0, 1, 12, 2, 0, NULL),
(10, 'Низкий', 'nizkij', 'prioritet/nizkij', 10, 0, 10, '2016-09-01 09:52:01.637618', '2016-09-01 09:53:00.597857', 'low', '', 1, 0, 2, 7, 2, 1, 9),
(11, 'Средний', 'srednij', 'prioritet/srednij', 10, 0, 10, '2016-09-01 09:52:36.38551', '2016-09-01 09:53:07.775504', 'middle', '', 1, 0, 8, 9, 2, 1, 9),
(12, 'Высокий', 'vysokij', 'prioritet/vysokij', 10, 0, 10, '2016-09-01 09:53:24.164271', '2016-09-01 09:53:24.164306', 'high', '', 1, 0, 10, 11, 2, 1, 9),
(13, 'Состояние', 'sostoyanie', 'sostoyanie', 20, 3, 30, '2016-09-01 10:06:52.402104', '2016-11-03 12:22:32.632364', NULL, '', 1, 0, 1, 8, 4, 0, NULL),
(14, 'Запланированно', 'zaplanirovanno', 'sostoyanie/zaplanirovanno', 10, 0, 10, '2016-09-01 10:07:22.437182', '2016-09-01 10:07:50.467462', NULL, '', 1, 0, 2, 3, 4, 1, 13),
(15, 'В процессе', 'v-processe', 'sostoyanie/v-processe', 10, 0, 10, '2016-09-01 10:07:33.700932', '2016-09-01 10:07:33.700965', NULL, '', 1, 0, 4, 5, 4, 1, 13),
(16, 'Завершено', 'zaversheno', 'sostoyanie/zaversheno', 10, 0, 10, '2016-09-01 10:08:11.591613', '2016-09-01 10:08:11.59166', NULL, '', 1, 0, 6, 7, 4, 1, 13),
(17, 'В течении недели', 'v-techenii-nedeli', 'prioritet/nizkij/v-techenii-nedeli', 10, 0, 20, '2016-09-02 09:35:07.26623', '2016-11-03 12:23:03.392563', NULL, '', 1, 0, 3, 4, 2, 2, 10),
(18, 'В течении месяца', 'v-techenii-mesyaca', 'prioritet/nizkij/v-techenii-mesyaca', 10, 0, 20, '2016-09-02 09:35:19.832931', '2016-10-10 19:53:58.821727', NULL, '', 1, 0, 5, 6, 2, 2, 10),
(19, 'Бюджет', 'byudzhet', 'napravlenie/finansy/byudzhet', 20, 0, 20, '2016-09-05 11:00:41.048763', '2016-11-03 12:23:34.095118', NULL, '', 1, 0, 7, 12, 3, 2, 7),
(20, 'Доходы', 'dohody', 'napravlenie/finansy/byudzhet/dohody', 10, 0, 10, '2016-09-05 11:01:31.631699', '2016-09-05 11:01:31.631758', NULL, '', 1, 0, 8, 9, 3, 3, 19),
(21, 'Расходы', 'rashody', 'napravlenie/finansy/rashody', 10, 0, 10, '2016-09-05 11:01:40.811848', '2016-09-05 11:01:40.811882', NULL, '', 1, 0, 10, 11, 3, 3, 19),
(22, 'Вид', 'vid', 'napravlenie/finansy/vid', 10, 0, 10, '2016-09-05 11:02:23.030871', '2016-09-05 11:04:27.619063', NULL, '', 1, 0, 13, 18, 3, 2, 7),
(23, 'Наличные', 'nalichnye', 'napravlenie/finansy/vid/nalichnye', 10, 0, 10, '2016-09-05 11:02:33.636101', '2016-09-05 11:02:33.636274', NULL, '', 1, 0, 14, 15, 3, 3, 22),
(24, 'Безналичный расчет', 'beznalichnyj-raschet', 'napravlenie/finansy/vid/beznalichnyj-raschet', 10, 0, 10, '2016-09-05 11:02:44.095637', '2016-09-05 11:02:44.09567', NULL, '', 1, 0, 16, 17, 3, 3, 22),
(25, 'Года', 'added-year', 'added-year', 20, 0, 10, '2016-09-23 13:28:00.554061', '2016-09-23 13:28:00.554107', NULL, NULL, 1, 63, 1, 4, 5, 0, NULL),
(26, 'Месяца', 'added-month', 'added-month', 10, 0, 10, '2016-09-23 13:28:00.631426', '2016-09-23 13:28:00.631487', NULL, NULL, 1, 63, 1, 26, 6, 0, NULL),
(27, 'Январь', 'added-month-01', 'added-month/added-month-01', 10, 0, 10, '2016-09-23 13:28:00.653716', '2016-09-23 13:28:00.653768', NULL, NULL, 1, 63, 2, 3, 6, 1, 26),
(28, 'Февраль', 'added-month-02', 'added-month/added-month-02', 10, 0, 10, '2016-09-23 13:28:00.679455', '2016-09-23 13:28:00.679498', NULL, NULL, 1, 63, 4, 5, 6, 1, 26),
(29, 'Март', 'added-month-03', 'added-month/added-month-03', 10, 0, 10, '2016-09-23 13:28:00.709434', '2016-09-23 13:28:00.709483', NULL, NULL, 1, 63, 6, 7, 6, 1, 26),
(30, 'Апрель', 'added-month-04', 'added-month/added-month-04', 10, 0, 10, '2016-09-23 13:28:00.732729', '2016-09-23 13:28:00.732785', NULL, NULL, 1, 63, 8, 9, 6, 1, 26),
(31, 'Май', 'added-month-05', 'added-month/added-month-05', 10, 0, 10, '2016-09-23 13:28:00.761781', '2016-09-23 13:28:00.761822', NULL, NULL, 1, 63, 10, 11, 6, 1, 26),
(32, 'Июнь', 'added-month-06', 'added-month/added-month-06', 10, 0, 10, '2016-09-23 13:28:00.790824', '2016-09-23 13:28:00.790873', NULL, NULL, 1, 63, 12, 13, 6, 1, 26),
(33, 'Июль', 'added-month-07', 'added-month/added-month-07', 10, 0, 10, '2016-09-23 13:28:00.819111', '2016-09-23 13:28:00.81915', NULL, NULL, 1, 63, 14, 15, 6, 1, 26),
(34, 'Август', 'added-month-08', 'added-month/added-month-08', 10, 0, 10, '2016-09-23 13:28:00.847194', '2016-09-23 13:28:00.847277', NULL, NULL, 1, 63, 16, 17, 6, 1, 26),
(35, 'Сентябрь', 'added-month-09', 'added-month/added-month-09', 10, 0, 10, '2016-09-23 13:28:00.87288', '2016-09-23 13:28:00.872935', NULL, NULL, 1, 63, 18, 19, 6, 1, 26),
(36, 'Октябрь', 'added-month-10', 'added-month/added-month-10', 10, 0, 10, '2016-09-23 13:28:00.895734', '2016-09-23 13:28:00.895806', NULL, NULL, 1, 63, 20, 21, 6, 1, 26),
(37, 'Ноябрь', 'added-month-11', 'added-month/added-month-11', 10, 0, 10, '2016-09-23 13:28:00.92597', '2016-09-23 13:28:00.926061', NULL, NULL, 1, 63, 22, 23, 6, 1, 26),
(38, 'Декабрь', 'added-month-12', 'added-month/added-month-12', 10, 0, 10, '2016-09-23 13:28:01.087545', '2016-09-23 13:28:01.08762', NULL, NULL, 1, 63, 24, 25, 6, 1, 26),
(39, 'Дни', 'added-day', 'added-day', 10, 0, 10, '2016-09-23 13:28:01.111478', '2016-09-23 13:28:01.111558', NULL, NULL, 1, 63, 1, 70, 7, 0, NULL),
(40, '1 - 10', 'added-day-01-10', 'added-day/added-day-01-10', 10, 0, 10, '2016-09-23 13:28:01.140287', '2016-11-24 14:27:39.610098', NULL, NULL, 1, 63, 2, 23, 7, 1, 39),
(41, '01', 'added-day-01', 'added-day/added-day-01-10/added-day-01', 10, 0, 10, '2016-09-23 13:28:01.160351', '2016-09-23 13:28:01.160403', NULL, NULL, 1, 63, 3, 4, 7, 2, 40),
(42, '02', 'added-day-02', 'added-day/added-day-01-10/added-day-02', 10, 0, 10, '2016-09-23 13:28:01.187035', '2016-09-23 13:28:01.187116', NULL, NULL, 1, 63, 5, 6, 7, 2, 40),
(43, '03', 'added-day-03', 'added-day/added-day-01-10/added-day-03', 10, 0, 10, '2016-09-23 13:28:01.208977', '2016-09-23 13:28:01.209015', NULL, NULL, 1, 63, 7, 8, 7, 2, 40),
(44, '04', 'added-day-04', 'added-day/added-day-01-10/added-day-04', 10, 0, 10, '2016-09-23 13:28:01.228546', '2016-09-23 13:28:01.228579', NULL, NULL, 1, 63, 9, 10, 7, 2, 40),
(45, '05', 'added-day-05', 'added-day/added-day-01-10/added-day-05', 10, 0, 10, '2016-09-23 13:28:01.257806', '2016-09-23 13:28:01.257889', NULL, NULL, 1, 63, 11, 12, 7, 2, 40),
(46, '06', 'added-day-06', 'added-day/added-day-01-10/added-day-06', 10, 0, 10, '2016-09-23 13:28:01.280884', '2016-09-23 13:28:01.280933', NULL, NULL, 1, 63, 13, 14, 7, 2, 40),
(47, '07', 'added-day-07', 'added-day/added-day-01-10/added-day-07', 10, 0, 10, '2016-09-23 13:28:01.302951', '2016-09-23 13:28:01.302997', NULL, NULL, 1, 63, 15, 16, 7, 2, 40),
(48, '08', 'added-day-08', 'added-day/added-day-01-10/added-day-08', 10, 0, 10, '2016-09-23 13:28:01.33147', '2016-09-23 13:28:01.331536', NULL, NULL, 1, 63, 17, 18, 7, 2, 40),
(49, '09', 'added-day-09', 'added-day/added-day-01-10/added-day-09', 10, 0, 10, '2016-09-23 13:28:01.35968', '2016-09-23 13:28:01.359762', NULL, NULL, 1, 63, 19, 20, 7, 2, 40),
(50, '10', 'added-day-10', 'added-day/added-day-01-10/added-day-10', 10, 0, 10, '2016-09-23 13:28:01.384093', '2016-09-23 13:28:01.384144', NULL, NULL, 1, 63, 21, 22, 7, 2, 40),
(51, '11 - 20', 'added-day-11-20', 'added-day/added-day-11-20', 10, 0, 10, '2016-09-23 13:28:01.414127', '2016-11-24 14:27:39.699279', NULL, NULL, 1, 63, 24, 45, 7, 1, 39),
(52, '11', 'added-day-11', 'added-day/added-day-11-20/added-day-11', 10, 0, 10, '2016-09-23 13:28:01.445561', '2016-09-23 13:28:01.445607', NULL, NULL, 1, 63, 25, 26, 7, 2, 51),
(53, '12', 'added-day-12', 'added-day/added-day-11-20/added-day-12', 10, 0, 10, '2016-09-23 13:28:01.472874', '2016-09-23 13:28:01.472923', NULL, NULL, 1, 63, 27, 28, 7, 2, 51),
(54, '13', 'added-day-13', 'added-day/added-day-11-20/added-day-13', 10, 0, 10, '2016-09-23 13:28:01.503398', '2016-09-23 13:28:01.503449', NULL, NULL, 1, 63, 29, 30, 7, 2, 51),
(55, '14', 'added-day-14', 'added-day/added-day-11-20/added-day-14', 10, 0, 10, '2016-09-23 13:28:01.526479', '2016-09-23 13:28:01.526521', NULL, NULL, 1, 63, 31, 32, 7, 2, 51),
(56, '15', 'added-day-15', 'added-day/added-day-11-20/added-day-15', 10, 0, 10, '2016-09-23 13:28:01.552312', '2016-09-23 13:28:01.55236', NULL, NULL, 1, 63, 33, 34, 7, 2, 51),
(57, '16', 'added-day-16', 'added-day/added-day-11-20/added-day-16', 10, 0, 10, '2016-09-23 13:28:01.608229', '2016-09-23 13:28:01.60828', NULL, NULL, 1, 63, 35, 36, 7, 2, 51),
(58, '17', 'added-day-17', 'added-day/added-day-11-20/added-day-17', 10, 0, 10, '2016-09-23 13:28:01.641438', '2016-09-23 13:28:01.64151', NULL, NULL, 1, 63, 37, 38, 7, 2, 51),
(59, '18', 'added-day-18', 'added-day/added-day-11-20/added-day-18', 10, 0, 10, '2016-09-23 13:28:01.668426', '2016-09-23 13:28:01.668473', NULL, NULL, 1, 63, 39, 40, 7, 2, 51),
(60, '19', 'added-day-19', 'added-day/added-day-11-20/added-day-19', 10, 0, 10, '2016-09-23 13:28:01.695856', '2016-09-23 13:28:01.695908', NULL, NULL, 1, 63, 41, 42, 7, 2, 51),
(61, '20', 'added-day-20', 'added-day/added-day-11-20/added-day-20', 10, 0, 10, '2016-09-23 13:28:01.749978', '2016-09-23 13:28:01.750031', NULL, NULL, 1, 63, 43, 44, 7, 2, 51),
(62, '21 - 31', 'added-day-21-31', 'added-day/added-day-21-31', 10, 0, 10, '2016-09-23 13:28:01.771803', '2016-11-24 14:27:39.719925', NULL, NULL, 1, 63, 46, 69, 7, 1, 39),
(63, '21', 'added-day-21', 'added-day/added-day-21-31/added-day-21', 10, 0, 10, '2016-09-23 13:28:01.79194', '2016-09-23 13:28:01.792006', NULL, NULL, 1, 63, 47, 48, 7, 2, 62),
(64, '22', 'added-day-22', 'added-day/added-day-21-31/added-day-22', 10, 0, 10, '2016-09-23 13:28:01.815635', '2016-09-23 13:28:01.815689', NULL, NULL, 1, 63, 49, 50, 7, 2, 62),
(65, '23', 'added-day-23', 'added-day/added-day-21-31/added-day-23', 10, 0, 10, '2016-09-23 13:28:01.841799', '2016-09-23 13:28:01.841855', NULL, NULL, 1, 63, 51, 52, 7, 2, 62),
(66, '24', 'added-day-24', 'added-day/added-day-21-31/added-day-24', 10, 0, 10, '2016-09-23 13:28:01.875387', '2016-09-23 13:28:01.875471', NULL, NULL, 1, 63, 53, 54, 7, 2, 62),
(67, '25', 'added-day-25', 'added-day/added-day-21-31/added-day-25', 10, 0, 10, '2016-09-23 13:28:01.897283', '2016-09-23 13:28:01.897327', NULL, NULL, 1, 63, 55, 56, 7, 2, 62),
(68, '26', 'added-day-26', 'added-day/added-day-21-31/added-day-26', 10, 0, 10, '2016-09-23 13:28:01.922843', '2016-09-23 13:28:01.922896', NULL, NULL, 1, 63, 57, 58, 7, 2, 62),
(69, '27', 'added-day-27', 'added-day/added-day-21-31/added-day-27', 10, 0, 10, '2016-09-23 13:28:01.943716', '2016-09-23 13:28:01.943754', NULL, NULL, 1, 63, 59, 60, 7, 2, 62),
(70, '28', 'added-day-28', 'added-day/added-day-21-31/added-day-28', 10, 0, 10, '2016-09-23 13:28:01.963936', '2016-09-23 13:28:01.963988', NULL, NULL, 1, 63, 61, 62, 7, 2, 62),
(71, '29', 'added-day-29', 'added-day/added-day-21-31/added-day-29', 10, 0, 10, '2016-09-23 13:28:01.988332', '2016-09-23 13:28:01.988407', NULL, NULL, 1, 63, 63, 64, 7, 2, 62),
(72, '30', 'added-day-30', 'added-day/added-day-21-31/added-day-30', 10, 0, 10, '2016-09-23 13:28:02.018269', '2016-09-23 13:28:02.01834', NULL, NULL, 1, 63, 65, 66, 7, 2, 62),
(73, '31', 'added-day-31', 'added-day/added-day-21-31/added-day-31', 10, 0, 10, '2016-09-23 13:28:02.041645', '2016-09-23 13:28:02.04168', NULL, NULL, 1, 63, 67, 68, 7, 2, 62),
(74, '2016', 'added-year-2016', 'added-year/added-year-2016', 10, 0, 10, '2016-11-15 11:20:37.920045', '2016-11-15 11:20:37.92012', NULL, NULL, 1, 63, 2, 3, 5, 1, 25),
(75, 'Зависит', 'zavisit', 'zavisit', 10, 4, 10, '2016-11-15 12:03:31.065013', '2016-11-15 12:03:31.06509', NULL, '', 1, 0, 1, 2, 8, 0, NULL);

-- 
-- Вывод данных для таблицы auth_permission
--
INSERT INTO auth_permission VALUES
(1, 'Can add permission', 1, 'add_permission'),
(2, 'Can change permission', 1, 'change_permission'),
(3, 'Can delete permission', 1, 'delete_permission'),
(4, 'Can add group', 2, 'add_group'),
(5, 'Can change group', 2, 'change_group'),
(6, 'Can delete group', 2, 'delete_group'),
(7, 'Can add Customer', 3, 'add_user'),
(8, 'Can change Customer', 3, 'change_user'),
(9, 'Can delete Customer', 3, 'delete_user'),
(10, 'Can add content type', 4, 'add_contenttype'),
(11, 'Can change content type', 4, 'change_contenttype'),
(12, 'Can delete content type', 4, 'delete_contenttype'),
(13, 'Can add session', 5, 'add_session'),
(14, 'Can change session', 5, 'change_session'),
(15, 'Can delete session', 5, 'delete_session'),
(16, 'Can add site', 6, 'add_site'),
(17, 'Can change site', 6, 'change_site'),
(18, 'Can delete site', 6, 'delete_site'),
(19, 'Can add log entry', 7, 'add_logentry'),
(20, 'Can change log entry', 7, 'change_logentry'),
(21, 'Can delete log entry', 7, 'delete_logentry'),
(22, 'Can add Token', 8, 'add_token'),
(23, 'Can change Token', 8, 'change_token'),
(24, 'Can delete Token', 8, 'delete_token'),
(25, 'Can add email', 9, 'add_email'),
(26, 'Can change email', 9, 'change_email'),
(27, 'Can delete email', 9, 'delete_email'),
(28, 'Can add log', 10, 'add_log'),
(29, 'Can change log', 10, 'change_log'),
(30, 'Can delete log', 10, 'delete_log'),
(31, 'Can add Email Template', 11, 'add_emailtemplate'),
(32, 'Can change Email Template', 11, 'change_emailtemplate'),
(33, 'Can delete Email Template', 11, 'delete_emailtemplate'),
(34, 'Can add attachment', 12, 'add_attachment'),
(35, 'Can change attachment', 12, 'change_attachment'),
(36, 'Can delete attachment', 12, 'delete_attachment'),
(37, 'Can add Folder', 13, 'add_folder'),
(38, 'Can change Folder', 13, 'change_folder'),
(39, 'Can delete Folder', 13, 'delete_folder'),
(40, 'Can use directory listing', 13, 'can_use_directory_listing'),
(41, 'Can add folder permission', 14, 'add_folderpermission'),
(42, 'Can change folder permission', 14, 'change_folderpermission'),
(43, 'Can delete folder permission', 14, 'delete_folderpermission'),
(44, 'Can add file', 15, 'add_file'),
(45, 'Can change file', 15, 'change_file'),
(46, 'Can delete file', 15, 'delete_file'),
(47, 'Can add clipboard', 16, 'add_clipboard'),
(48, 'Can change clipboard', 16, 'change_clipboard'),
(49, 'Can delete clipboard', 16, 'delete_clipboard'),
(50, 'Can add clipboard item', 17, 'add_clipboarditem'),
(51, 'Can change clipboard item', 17, 'change_clipboarditem'),
(52, 'Can delete clipboard item', 17, 'delete_clipboarditem'),
(53, 'Can add image', 18, 'add_image'),
(54, 'Can change image', 18, 'change_image'),
(55, 'Can delete image', 18, 'delete_image'),
(56, 'Can add thumbnail option', 19, 'add_thumbnailoption'),
(57, 'Can change thumbnail option', 19, 'change_thumbnailoption'),
(58, 'Can delete thumbnail option', 19, 'delete_thumbnailoption'),
(59, 'Can add source', 20, 'add_source'),
(60, 'Can change source', 20, 'change_source'),
(61, 'Can delete source', 20, 'delete_source'),
(62, 'Can add thumbnail', 21, 'add_thumbnail'),
(63, 'Can change thumbnail', 21, 'change_thumbnail'),
(64, 'Can delete thumbnail', 21, 'delete_thumbnail'),
(65, 'Can add thumbnail dimensions', 22, 'add_thumbnaildimensions'),
(66, 'Can change thumbnail dimensions', 22, 'change_thumbnaildimensions'),
(67, 'Can delete thumbnail dimensions', 22, 'delete_thumbnaildimensions'),
(68, 'Can add customer', 23, 'add_customer'),
(69, 'Can change customer', 23, 'change_customer'),
(70, 'Can delete customer', 23, 'delete_customer'),
(71, 'Can add Term', 24, 'add_term'),
(72, 'Can change Term', 24, 'change_term'),
(73, 'Can delete Term', 24, 'delete_term'),
(74, 'Can add Data mart', 25, 'add_datamart'),
(75, 'Can change Data mart', 25, 'change_datamart'),
(76, 'Can delete Data mart', 25, 'delete_datamart'),
(77, 'Can add Additional Entity Characteristic or Mark', 26, 'add_additionalentitycharacteristicormark'),
(78, 'Can change Additional Entity Characteristic or Mark', 26, 'change_additionalentitycharacteristicormark'),
(79, 'Can delete Additional Entity Characteristic or Mark', 26, 'delete_additionalentitycharacteristicormark'),
(80, 'Can add Todo', 27, 'add_todo'),
(81, 'Can change Todo', 27, 'change_todo'),
(82, 'Can delete Todo', 27, 'delete_todo'),
(83, 'Can add Customer', 3, 'add_customerproxy'),
(84, 'Can change Customer', 3, 'change_customerproxy'),
(85, 'Can delete Customer', 3, 'delete_customerproxy'),
(86, 'Can add Entity Relation', 29, 'add_entityrelation'),
(87, 'Can change Entity Relation', 29, 'change_entityrelation'),
(88, 'Can delete Entity Relation', 29, 'delete_entityrelation'),
(89, 'Can add Entity Image', 30, 'add_entityimage'),
(90, 'Can change Entity Image', 30, 'change_entityimage'),
(91, 'Can delete Entity Image', 30, 'delete_entityimage'),
(92, 'Can add Notification', 32, 'add_notification'),
(93, 'Can change Notification', 32, 'change_notification'),
(94, 'Can delete Notification', 32, 'delete_notification'),
(95, 'Can add Attachment', 33, 'add_notificationattachment'),
(96, 'Can change Attachment', 33, 'change_notificationattachment'),
(97, 'Can delete Attachment', 33, 'delete_notificationattachment'),
(98, 'Can add Related data mart', 34, 'add_entityrelateddatamart'),
(99, 'Can change Related data mart', 34, 'change_entityrelateddatamart'),
(100, 'Can delete Related data mart', 34, 'delete_entityrelateddatamart'),
(101, 'Can add Data mart relation', 35, 'add_datamartrelation'),
(102, 'Can change Data mart relation', 35, 'change_datamartrelation'),
(103, 'Can delete Data mart relation', 35, 'delete_datamartrelation');

-- 
-- Вывод данных для таблицы auth_user_groups
--

-- Таблица edw_todos_db.auth_user_groups не содержит данных

-- 
-- Вывод данных для таблицы authtoken_token
--

-- Таблица edw_todos_db.authtoken_token не содержит данных

-- 
-- Вывод данных для таблицы django_admin_log
--
INSERT INTO django_admin_log VALUES
(28, '2016-09-05 11:47:17.651705', '1', 'root', 2, 'Изменены salutation и recognized для customer "root".', 28, 2),
(29, '2016-09-05 11:47:35.298098', '1', 'root', 2, 'Изменены salutation для customer "root".', 28, 2),
(30, '2016-09-05 11:47:44.686374', '2', 'rufus', 2, 'Изменены salutation для customer "rufus".', 28, 2),
(31, '2016-09-05 11:48:51.467027', '1', 'root', 3, '', 28, 2),
(32, '2016-09-05 11:53:11.360397', '2', 'Личные', 2, 'Изменен system_flags и terms.', 25, 3),
(33, '2016-09-05 11:53:36.354077', '2', 'Личные', 2, 'Изменен system_flags и terms.', 25, 3),
(34, '2016-09-05 11:57:26.7807', '2', 'Личные', 2, 'Изменен system_flags и terms.', 25, 3),
(35, '2016-09-05 12:15:00.154841', '2', 'Личные', 2, 'Изменен system_flags и terms.', 25, 3),
(36, '2016-09-05 12:19:07.123964', '2', 'Личные', 2, 'Изменен system_flags и terms.', 25, 3),
(37, '2016-09-05 18:22:00.885474', '2', 'Личные', 2, 'Изменен system_flags.', 25, 3),
(38, '2016-09-05 18:22:45.885662', '2', 'Личные', 2, 'Изменен system_flags и terms.', 25, 3),
(39, '2016-09-05 18:33:09.600146', '2', 'Личные', 2, 'Изменен system_flags и terms.', 25, 3),
(40, '2016-09-05 18:54:19.844639', '2', 'Личные', 2, 'Изменен system_flags.', 25, 3),
(41, '2016-09-05 18:54:37.107396', '2', 'Личные', 2, 'Изменен system_flags и terms.', 25, 3),
(42, '2016-09-05 18:56:04.794083', '2', 'Личные', 2, 'Изменен system_flags.', 25, 3),
(43, '2016-09-05 18:56:19.013633', '2', 'Личные', 2, 'Изменен system_flags и terms.', 25, 3),
(44, '2016-09-05 18:59:26.812911', '2', 'Личные', 2, 'Изменен system_flags и terms.', 25, 3),
(45, '2016-09-05 18:59:49.75041', '2', 'Личные', 2, 'Изменен system_flags.', 25, 3),
(46, '2016-09-05 19:00:04.026566', '2', 'Личные', 2, 'Изменен system_flags и terms.', 25, 3),
(47, '2016-09-05 19:46:12.381817', '2', 'Личные', 2, 'Изменен system_flags и terms.', 25, 3),
(48, '2016-09-05 19:53:44.541699', '2', 'Личные', 2, 'Изменен system_flags и terms.', 25, 3),
(49, '2016-09-05 19:58:21.31385', '2', 'Личные', 2, 'Изменен system_flags.', 25, 3),
(50, '2016-09-05 19:58:36.81995', '2', 'Личные', 2, 'Изменен system_flags и terms.', 25, 3),
(51, '2016-09-05 19:59:00.090596', '2', 'Личные', 2, 'Изменен system_flags и terms.', 25, 3),
(52, '2016-09-05 20:06:01.803972', '2', 'Личные', 2, 'Изменен system_flags и terms.', 25, 3),
(53, '2016-09-05 20:06:47.071008', '4', 'w', 1, 'Добавлено.', 25, 3),
(54, '2016-09-05 20:17:26.693577', '4', 'w', 2, 'Изменен system_flags и terms.', 25, 3),
(55, '2016-09-05 20:18:39.122315', '4', 'w', 2, 'Изменен system_flags и terms.', 25, 3),
(56, '2016-09-05 20:40:40.354251', '4', 'w', 2, 'Изменен system_flags и terms.', 25, 3),
(57, '2016-09-05 20:47:06.423802', '4', 'w', 2, 'Изменен system_flags и terms.', 25, 3),
(58, '2016-09-05 20:47:12.579968', '4', 'w', 2, 'Изменен system_flags и terms.', 25, 3),
(59, '2016-09-05 20:47:39.052819', '4', 'w', 2, 'Изменен system_flags и terms.', 25, 3),
(60, '2016-09-05 20:47:59.306484', '4', 'w', 2, 'Изменен system_flags и terms.', 25, 3),
(61, '2016-09-05 20:48:06.925653', '4', 'w', 2, 'Изменен system_flags и terms.', 25, 3),
(62, '2016-09-05 21:02:14.662629', '4', 'w', 2, 'Изменен system_flags и terms.', 25, 3),
(63, '2016-09-05 21:02:23.568143', '4', 'w', 2, 'Изменен system_flags и terms.', 25, 3),
(64, '2016-09-05 21:02:28.225706', '4', 'w', 2, 'Изменен system_flags и terms.', 25, 3),
(65, '2016-09-05 21:02:37.940714', '4', 'w', 2, 'Изменен system_flags и terms.', 25, 3),
(66, '2016-09-05 21:02:48.889604', '4', 'w', 2, 'Изменен system_flags и terms.', 25, 3),
(67, '2016-09-05 21:07:12.386614', '4', 'w', 2, 'Изменен system_flags и terms.', 25, 3),
(68, '2016-09-05 21:07:17.660506', '4', 'w', 2, 'Изменен system_flags и terms.', 25, 3),
(69, '2016-09-05 21:07:30.696048', '4', 'w', 2, 'Изменен system_flags и terms.', 25, 3),
(70, '2016-09-05 21:07:36.93508', '4', 'w', 2, 'Изменен system_flags и terms.', 25, 3),
(71, '2016-09-05 21:43:42.880293', '4', 'w', 2, 'Изменен system_flags и terms.', 25, 3),
(72, '2016-09-05 21:44:58.639997', '4', 'w', 2, 'Изменен system_flags.', 25, 3),
(73, '2016-09-05 21:45:11.726868', '5', 's', 1, 'Добавлено.', 25, 3),
(74, '2016-09-05 21:58:11.153918', '4', 'w', 3, '', 25, 3),
(75, '2016-09-05 21:58:19.520588', '5', 's', 3, '', 25, 3),
(76, '2016-09-05 22:01:15.092278', '6', 'w', 1, 'Добавлено.', 25, 3),
(77, '2016-09-05 22:01:39.899228', '6', 'w', 3, '', 25, 3),
(78, '2016-09-06 18:57:18.062555', '2', 'Провести сверку по дебиторам', 2, 'Ни одно поле не изменено.', 27, 3),
(79, '2016-09-06 19:02:57.300741', '16', '1', 1, 'Добавлено.', 27, 3),
(80, '2016-09-06 19:03:55.899907', '16', '1', 2, 'Ни одно поле не изменено.', 27, 3),
(81, '2016-09-06 19:04:01.849023', '17', '2', 1, 'Добавлено.', 27, 3),
(82, '2016-09-06 19:11:18.993524', '18', '122', 1, 'Добавлено.', 27, 3),
(83, '2016-09-07 10:43:14.343316', '3', 'root', 2, 'Изменен password.', 28, 2),
(84, '2016-09-07 10:43:27.737364', '3', 'root', 2, 'Изменены salutation для customer "root".', 28, 2),
(85, '2016-09-07 10:51:10.311421', '16', '1', 3, '', 27, 3),
(86, '2016-09-07 10:51:10.315071', '17', '2', 3, '', 27, 3),
(87, '2016-09-07 10:51:10.317691', '18', '122', 3, '', 27, 3),
(88, '2016-09-07 10:51:19.323597', '19', '1', 1, 'Добавлено.', 27, 3),
(89, '2016-09-07 10:51:31.055902', '19', '1', 2, 'Изменен terms.', 27, 3),
(90, '2016-09-15 16:12:22.348595', '15', 'Получить скидку', 2, 'Ни одно поле не изменено.', 27, 3),
(91, '2016-10-10 19:53:45.789139', '1', 'Вид', 2, 'Changed attributes, specification_mode and system_flags.', 24, 3),
(92, '2016-10-10 19:53:58.823592', '18', 'В течении месяца', 2, 'Changed attributes, specification_mode and system_flags.', 24, 3),
(93, '2016-11-03 11:28:17.474588', '7', 'Финансы', 2, 'Changed attributes, specification_mode and system_flags.', 24, 3),
(94, '2016-11-03 12:07:37.807683', '7', 'Финансы', 2, 'Changed attributes, description and system_flags.', 24, 3),
(95, '2016-11-03 12:22:32.635179', '13', 'Состояние', 2, 'Changed attributes, specification_mode and system_flags.', 24, 3),
(96, '2016-11-03 12:23:03.394644', '17', 'В течении недели', 2, 'Changed attributes, specification_mode and system_flags.', 24, 3),
(97, '2016-11-03 12:23:34.097341', '19', 'Бюджет', 2, 'Changed attributes, specification_mode and system_flags.', 24, 3),
(98, '2016-11-11 12:53:32.47623', '7', 'Финансы', 2, 'Changed attributes, specification_mode and system_flags.', 24, 3),
(99, '2016-11-11 13:04:55.819464', '1', 'Вид', 2, 'Changed attributes, description and system_flags.', 24, 3),
(100, '2016-11-15 11:28:01.441133', '1', 'Срочные дела', 2, 'Changed system_flags and terms.', 25, 3),
(101, '2016-11-15 12:03:31.0722', '75', 'Зависит', 1, 'Added.', 24, 3),
(102, '2016-11-15 12:04:27.201002', '5', 'Сходить к стоматологу', 2, 'Added Entity Relation "Сходить к стоматологу → Зависит → Провести сверку по дебиторам".', 27, 3);

-- 
-- Вывод данных для таблицы easy_thumbnails_thumbnail
--

-- Таблица edw_todos_db.easy_thumbnails_thumbnail не содержит данных

-- 
-- Вывод данных для таблицы filer_clipboard
--
INSERT INTO filer_clipboard VALUES
(1, 3);

-- 
-- Вывод данных для таблицы filer_folder
--

-- Таблица edw_todos_db.filer_folder не содержит данных

-- 
-- Вывод данных для таблицы post_office_email
--

-- Таблица edw_todos_db.post_office_email не содержит данных

-- 
-- Вывод данных для таблицы todos_customer
--
INSERT INTO todos_customer VALUES
(2, 2, 'na', '2016-09-07 10:43:27.883189', '{}', NULL),
(3, 2, 'na', '2016-11-16 16:15:30.297283', '{}', NULL);

-- 
-- Вывод данных для таблицы todos_datamart
--
INSERT INTO todos_datamart VALUES
(1, 'Срочные дела', 'srochnye-dela', 'srochnye-dela', '2016-09-02 08:52:23.964205', '2016-11-15 11:28:01.42219', NULL, '', 1, 0, 1, 6, 1, 0, NULL, 25, '-created_at', NULL),
(2, 'Личные', 'lichnye', 'srochnye-dela/lichnye', '2016-09-02 09:33:27.488956', '2016-09-05 20:06:01.796186', NULL, '', 1, 0, 2, 3, 1, 1, 1, 25, '-created_at', NULL),
(3, 'Рабочие', 'rabochie', 'srochnye-dela/rabochie', '2016-09-02 09:34:26.813196', '2016-09-02 09:34:26.813235', NULL, '', 1, 0, 4, 5, 1, 1, 1, 25, '-created_at', NULL);

-- 
-- Вывод данных для таблицы todos_notification
--

-- Таблица edw_todos_db.todos_notification не содержит данных

-- 
-- Вывод данных для таблицы todos_todo
--
INSERT INTO todos_todo VALUES
(2, '2016-09-01 09:59:24.193448', '2016-11-15 11:22:12.63101', 1, 'Провести сверку по дебиторам', 0, 2, 3, '<p>Сделать до отчета сверку по всем дебиторам.&nbsp;</p>', 2, 27),
(3, '2016-09-01 10:01:55.823774', '2016-09-02 08:01:14.896353', 1, 'Навести порядок на рабочем месте', 0, 1, NULL, '<p>Сдать в архив все закрытые сделки. Рассортировать всю текущую документацию по приоритетам. Всю&nbsp;документацию не нужную в текущей работе убрать или уничтожить при окончании срока хранения.</p>', 4, 27),
(5, '2016-09-01 10:03:45', '2016-11-15 12:04:27.167853', 1, 'Сходить к стоматологу', 0, 2, 1, '<p>Записаться и наконец сходить к зубному.</p>', 2, 27),
(6, '2016-09-01 10:04:45.71809', '2016-09-01 22:53:18.365563', 1, 'Помочь ребенку с подготовкой к экзамену', 1, 3, 2, '', 4, 27),
(7, '2016-09-01 10:06:05.324555', '2016-11-03 11:21:26.724515', 1, 'Съездить на рыбалку в выходные', 0, 3, 4, '<p>Собрать всех своих к субботе.</p>', 3, 27),
(15, '2016-09-01 23:50:52', '2016-11-15 11:22:13.513666', 1, 'Получить скидку', 0, 3, 3, '', 1, 27);

-- 
-- Вывод данных для таблицы auth_group_permissions
--

-- Таблица edw_todos_db.auth_group_permissions не содержит данных

-- 
-- Вывод данных для таблицы auth_user_user_permissions
--

-- Таблица edw_todos_db.auth_user_user_permissions не содержит данных

-- 
-- Вывод данных для таблицы easy_thumbnails_thumbnaildimensions
--

-- Таблица edw_todos_db.easy_thumbnails_thumbnaildimensions не содержит данных

-- 
-- Вывод данных для таблицы filer_file
--

-- Таблица edw_todos_db.filer_file не содержит данных

-- 
-- Вывод данных для таблицы filer_folderpermission
--

-- Таблица edw_todos_db.filer_folderpermission не содержит данных

-- 
-- Вывод данных для таблицы post_office_attachment_emails
--

-- Таблица edw_todos_db.post_office_attachment_emails не содержит данных

-- 
-- Вывод данных для таблицы post_office_log
--

-- Таблица edw_todos_db.post_office_log не содержит данных

-- 
-- Вывод данных для таблицы todos_additionalentitycharacteristicormark
--

-- Таблица edw_todos_db.todos_additionalentitycharacteristicormark не содержит данных

-- 
-- Вывод данных для таблицы todos_datamart_terms
--
INSERT INTO todos_datamart_terms VALUES
(1, 1, 1),
(5, 1, 4),
(44, 1, 9),
(45, 1, 13),
(46, 1, 25),
(20, 2, 2),
(38, 2, 5),
(39, 2, 6),
(35, 2, 8),
(18, 2, 11),
(24, 2, 14),
(40, 2, 17),
(32, 2, 21),
(43, 2, 22),
(11, 3, 2),
(12, 3, 4),
(10, 3, 12),
(13, 3, 13);

-- 
-- Вывод данных для таблицы todos_datamartrelation
--

-- Таблица edw_todos_db.todos_datamartrelation не содержит данных

-- 
-- Вывод данных для таблицы todos_entityrelateddatamart
--

-- Таблица edw_todos_db.todos_entityrelateddatamart не содержит данных

-- 
-- Вывод данных для таблицы todos_entityrelation
--
INSERT INTO todos_entityrelation VALUES
(1, 5, 75, 2);

-- 
-- Вывод данных для таблицы todos_todo_terms
--
INSERT INTO todos_todo_terms VALUES
(15, 2, 2),
(14, 2, 7),
(16, 2, 11),
(17, 2, 15),
(26, 3, 2),
(29, 3, 7),
(27, 3, 10),
(28, 3, 14),
(10, 5, 3),
(12, 5, 5),
(11, 5, 11),
(13, 5, 14),
(43, 5, 35),
(44, 5, 41),
(42, 5, 74),
(23, 6, 3),
(25, 6, 6),
(24, 6, 12),
(22, 6, 16),
(19, 7, 3),
(18, 7, 8),
(20, 7, 12),
(21, 7, 15),
(30, 15, 3),
(33, 15, 7),
(31, 15, 12),
(32, 15, 14);

-- 
-- Вывод данных для таблицы filer_clipboarditem
--

-- Таблица edw_todos_db.filer_clipboarditem не содержит данных

-- 
-- Вывод данных для таблицы filer_image
--

-- Таблица edw_todos_db.filer_image не содержит данных

-- 
-- Вывод данных для таблицы todos_notificationattachment
--

-- Таблица edw_todos_db.todos_notificationattachment не содержит данных

-- 
-- Вывод данных для таблицы todos_entityimage
--

-- Таблица edw_todos_db.todos_entityimage не содержит данных

-- 
-- Восстановить предыдущий режим SQL (SQL mode)
-- 
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;

-- 
-- Включение внешних ключей
-- 
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
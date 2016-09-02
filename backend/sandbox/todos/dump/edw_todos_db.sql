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
AUTO_INCREMENT = 2
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
AUTO_INCREMENT = 29
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
AUTO_INCREMENT = 32
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
AVG_ROW_LENGTH = 4096
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
AVG_ROW_LENGTH = 16384
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
AUTO_INCREMENT = 17
AVG_ROW_LENGTH = 1024
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
AUTO_INCREMENT = 86
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
AUTO_INCREMENT = 14
AVG_ROW_LENGTH = 1260
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
AUTO_INCREMENT = 1
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
AUTO_INCREMENT = 2
AVG_ROW_LENGTH = 16384
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
AUTO_INCREMENT = 23
AVG_ROW_LENGTH = 2730
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
AUTO_INCREMENT = 6
AVG_ROW_LENGTH = 3276
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
AUTO_INCREMENT = 34
AVG_ROW_LENGTH = 682
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
-- Вывод данных для таблицы auth_group
--

-- Таблица edw_todos_db.auth_group не содержит данных

--
-- Вывод данных для таблицы auth_user
--
INSERT INTO auth_user VALUES
(1, 'pbkdf2_sha256$24000$kBnFkZ9Q4fh7$kaU11ff/NKfcZT5MMerFg1wNi179z89E8hKMxlxmh3E=', '2016-09-02 08:00:33.600457', 1, 'root', '', '', 'team@infolabs.ru', 1, 1, '2016-09-01 22:16:06.038951');

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
(31, 'todos', '0002_remove_todo_slug', '2016-09-02 08:23:00.506776');

--
-- Вывод данных для таблицы django_session
--
INSERT INTO django_session VALUES
('buz9ekli1ancfjh2pndoxt5g06hwzlyc', 'OGFjNjIyN2YzZTViNDdhNGJjMGJiOWE3OTlkNjM2MmVmYjcyOGNkMjp7Il9hdXRoX3VzZXJfaGFzaCI6IjJjNDhmN2ZiYWY3MDRmOTMxZDg1ZDI3NWVmYTU1Mzc5ZTk3MTk1ZGUiLCJfYXV0aF91c2VyX2JhY2tlbmQiOiJkamFuZ28uY29udHJpYi5hdXRoLmJhY2tlbmRzLk1vZGVsQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOiIxIn0=', '2016-09-15 22:40:13.198928'),
('gy9xv0v1n2zpq6qv9zdw5c7xk9f8c16a', 'OGFjNjIyN2YzZTViNDdhNGJjMGJiOWE3OTlkNjM2MmVmYjcyOGNkMjp7Il9hdXRoX3VzZXJfaGFzaCI6IjJjNDhmN2ZiYWY3MDRmOTMxZDg1ZDI3NWVmYTU1Mzc5ZTk3MTk1ZGUiLCJfYXV0aF91c2VyX2JhY2tlbmQiOiJkamFuZ28uY29udHJpYi5hdXRoLmJhY2tlbmRzLk1vZGVsQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOiIxIn0=', '2016-09-16 08:56:19.244507'),
('sfx9ukrnsu1r3fyct63zm27ymqfrodm9', 'MWMxOTc5NTlmMDA4YzRjMWUwODNkZGNhZWNlODI5MTY2YjY0OGQ4Yjp7Il9hdXRoX3VzZXJfaGFzaCI6IjJjNDhmN2ZiYWY3MDRmOTMxZDg1ZDI3NWVmYTU1Mzc5ZTk3MTk1ZGUiLCJfYXV0aF91c2VyX2lkIjoiMSIsIl9hdXRoX3VzZXJfYmFja2VuZCI6ImRqYW5nby5jb250cmliLmF1dGguYmFja2VuZHMuTW9kZWxCYWNrZW5kIn0=', '2016-09-15 23:14:14.483252');

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
(1, 'Вид', 'vid', 'vid', 20, 1, 10, '2016-09-01 09:48:31.866896', '2016-09-01 09:48:31.866931', NULL, '', 1, 0, 1, 6, 1, 0, NULL),
(2, 'Рабочее', 'rabochee', 'vid/rabochee', 30, 0, 10, '2016-09-01 09:49:07.287624', '2016-09-01 09:55:15.498308', NULL, '', 1, 0, 2, 3, 1, 1, 1),
(3, 'Личное', 'lichnoe', 'vid/lichnoe', 30, 0, 10, '2016-09-01 09:49:14.267012', '2016-09-01 09:55:21.978142', NULL, '', 1, 0, 4, 5, 1, 1, 1),
(4, 'Направление', 'napravlenie', 'napravlenie', 10, 1, 10, '2016-09-01 09:49:30.998872', '2016-09-01 22:50:15.716412', 'direction', '', 1, 0, 1, 10, 3, 0, NULL),
(5, 'Здоровье', 'zdorove', 'napravlenie/zdorove', 10, 0, 10, '2016-09-01 09:50:11.904556', '2016-09-01 09:53:51.103124', 'health', '', 1, 0, 2, 3, 3, 1, 4),
(6, 'Семья', 'semya', 'napravlenie/semya', 10, 0, 10, '2016-09-01 09:50:28.052175', '2016-09-01 09:54:05.129704', 'family', '', 1, 0, 4, 5, 3, 1, 4),
(7, 'Финансы', 'finansy', 'napravlenie/finansy', 10, 0, 10, '2016-09-01 09:50:56.260197', '2016-09-01 09:54:13.330201', 'finance', '', 1, 0, 6, 7, 3, 1, 4),
(8, 'Хобби', 'hobbi', 'napravlenie/hobbi', 10, 0, 10, '2016-09-01 09:51:09.908891', '2016-09-01 09:54:20.580387', 'hobby', '', 1, 0, 8, 9, 3, 1, 4),
(9, 'Приоритет', 'prioritet', 'prioritet', 20, 3, 10, '2016-09-01 09:51:33.267616', '2016-09-01 09:52:52.639264', 'priority', '', 1, 0, 1, 8, 2, 0, NULL),
(10, 'Низкий', 'nizkij', 'prioritet/nizkij', 10, 0, 10, '2016-09-01 09:52:01.637618', '2016-09-01 09:53:00.597857', 'low', '', 1, 0, 2, 3, 2, 1, 9),
(11, 'Средний', 'srednij', 'prioritet/srednij', 10, 0, 10, '2016-09-01 09:52:36.38551', '2016-09-01 09:53:07.775504', 'middle', '', 1, 0, 4, 5, 2, 1, 9),
(12, 'Высокий', 'vysokij', 'prioritet/vysokij', 10, 0, 10, '2016-09-01 09:53:24.164271', '2016-09-01 09:53:24.164306', 'high', '', 1, 0, 6, 7, 2, 1, 9),
(13, 'Состояние', 'sostoyanie', 'sostoyanie', 20, 3, 10, '2016-09-01 10:06:52.402104', '2016-09-01 10:07:58.103911', NULL, '', 1, 0, 1, 8, 4, 0, NULL),
(14, 'Запланированно', 'zaplanirovanno', 'sostoyanie/zaplanirovanno', 10, 0, 10, '2016-09-01 10:07:22.437182', '2016-09-01 10:07:50.467462', NULL, '', 1, 0, 2, 3, 4, 1, 13),
(15, 'В процессе', 'v-processe', 'sostoyanie/v-processe', 10, 0, 10, '2016-09-01 10:07:33.700932', '2016-09-01 10:07:33.700965', NULL, '', 1, 0, 4, 5, 4, 1, 13),
(16, 'Завершено', 'zaversheno', 'sostoyanie/zaversheno', 10, 0, 10, '2016-09-01 10:08:11.591613', '2016-09-01 10:08:11.59166', NULL, '', 1, 0, 6, 7, 4, 1, 13);

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
(85, 'Can delete Customer', 3, 'delete_customerproxy');

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
(1, '2016-09-01 22:21:47.817577', '4', 'Заплатить квартплату', 2, 'Изменен marked, priority и direction.', 27, 1),
(2, '2016-09-01 22:50:15.718432', '4', 'Направление', 2, 'Изменен semantic_rule, attributes и system_flags.', 24, 1),
(3, '2016-09-01 22:50:42.804388', '4', 'Заплатить квартплату', 2, 'Изменен terms.', 27, 1),
(4, '2016-09-01 22:51:20.708306', '1', 'Закончить сделку с клиентом', 2, 'Изменен priority, direction и terms.', 27, 1),
(5, '2016-09-01 22:51:50.00505', '5', 'Сходить к стоматологу', 2, 'Изменен priority, direction и terms.', 27, 1),
(6, '2016-09-01 22:52:16.727998', '2', 'Провести сверку по дебиторам', 2, 'Изменен priority, direction и terms.', 27, 1),
(7, '2016-09-01 22:52:51.345351', '7', 'Съездить на рыбалку в выходные', 2, 'Изменен marked, priority, direction и terms.', 27, 1),
(8, '2016-09-01 22:53:18.370517', '6', 'Помочь ребенку с подготовкой к экзамену', 2, 'Изменен marked, priority, direction и terms.', 27, 1),
(9, '2016-09-01 22:54:06.131324', '3', 'Навести порядок на рабочем месте', 2, 'Изменен priority и terms.', 27, 1),
(10, '2016-09-01 23:01:24.869458', '8', 'Тест', 3, '', 27, 1),
(11, '2016-09-02 07:43:24.051789', '15', 'Получить скидку', 2, 'Изменен name, slug, priority, direction и terms.', 27, 1),
(12, '2016-09-02 08:24:09.901236', '17', '123', 2, 'Изменен name.', 27, 1),
(13, '2016-09-02 08:52:23.971261', '1', 'Срочные дела', 1, 'Добавлено.', 25, 1);

--
-- Вывод данных для таблицы easy_thumbnails_thumbnail
--

-- Таблица edw_todos_db.easy_thumbnails_thumbnail не содержит данных

--
-- Вывод данных для таблицы filer_clipboard
--

-- Таблица edw_todos_db.filer_clipboard не содержит данных

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
(1, 2, '', '2016-09-02 08:56:11.653979', '{}', NULL);

--
-- Вывод данных для таблицы todos_datamart
--
INSERT INTO todos_datamart VALUES
(1, 'Срочные дела', 'srochnye-dela', 'srochnye-dela', '2016-09-02 08:52:23.964205', '2016-09-02 08:52:23.964237', NULL, '', 1, 0, 1, 2, 1, 0, NULL, 25);

--
-- Вывод данных для таблицы todos_todo
--
INSERT INTO todos_todo VALUES
(2, '2016-09-01 09:59:24.193448', '2016-09-01 23:51:06.532967', 1, 'Провести сверку по дебиторам', 0, 2, 3, '<p>Сделать до отчета сверку по всем дебиторам.&nbsp;</p>', 2, 27),
(3, '2016-09-01 10:01:55.823774', '2016-09-02 08:01:14.896353', 1, 'Навести порядок на рабочем месте', 0, 1, NULL, '<p>Сдать в архив все закрытые сделки. Рассортировать всю текущую документацию по приоритетам. Всю&nbsp;документацию не нужную в текущей работе убрать или уничтожить при окончании срока хранения.</p>', 4, 27),
(5, '2016-09-01 10:03:45.694074', '2016-09-01 23:35:56.409812', 1, 'Сходить к стоматологу', 0, 2, 1, '<p>Записаться и наконец сходить к зубному.</p>', 2, 27),
(6, '2016-09-01 10:04:45.71809', '2016-09-01 22:53:18.365563', 1, 'Помочь ребенку с подготовкой к экзамену', 1, 3, 2, '', 4, 27),
(7, '2016-09-01 10:06:05.324555', '2016-09-02 08:01:26.109404', 1, 'Съездить на рыбалку в выходные', 1, 3, 4, '<p>Собрать всех своих к субботе.</p>', 3, 27),
(15, '2016-09-01 23:50:52.748865', '2016-09-02 08:26:16.20303', 1, 'Получить скидку', 1, 3, 3, '', 1, 27);

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
(3, 1, 12),
(4, 1, 14),
(2, 1, 15);

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
-- Восстановить предыдущий режим SQL (SQL mode)
--
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;

--
-- Включение внешних ключей
--
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
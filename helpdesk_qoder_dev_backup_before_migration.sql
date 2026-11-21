-- Backup of helpdesk_qoder_dev taken before migration
-- Table: alembic_version
-- Row count: 1
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO `alembic_version` (version_num) VALUES ("a1b2c3d4e5f6");
-- Table: attachments
-- Row count: 0
CREATE TABLE `attachments` (
  `complaint_id` int NOT NULL,
  `user_id` int NOT NULL,
  `original_filename` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `stored_filename` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `storage_path` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL,
  `file_size` int NOT NULL,
  `mime_type` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `file_extension` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `is_confidential` tinyint(1) NOT NULL,
  `download_count` int NOT NULL,
  `last_downloaded_at` datetime DEFAULT NULL,
  `last_downloaded_by_user_id` int DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  `created_by_user_id` int DEFAULT NULL,
  `updated_by_user_id` int DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted_by_user_id` int DEFAULT NULL,
  `version` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_attachments_stored_filename` (`stored_filename`),
  KEY `ix_attachments_complaint_id` (`complaint_id`),
  KEY `fk_attachments_last_downloaded_by_user_id_users` (`last_downloaded_by_user_id`),
  KEY `fk_attachments_user_id_users` (`user_id`),
  CONSTRAINT `fk_attachments_complaint_id_complaints` FOREIGN KEY (`complaint_id`) REFERENCES `complaints` (`id`),
  CONSTRAINT `fk_attachments_last_downloaded_by_user_id_users` FOREIGN KEY (`last_downloaded_by_user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_attachments_user_id_users` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
-- Table: audit_logs
-- Row count: 34
CREATE TABLE `audit_logs` (
  `user_id` int DEFAULT NULL,
  `session_id` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `ip_address` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `user_agent` text COLLATE utf8mb4_unicode_ci,
  `request_id` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `action` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `entity_type` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `entity_id` int DEFAULT NULL,
  `entity_repr` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `old_values` json DEFAULT NULL,
  `new_values` json DEFAULT NULL,
  `changed_fields` json DEFAULT NULL,
  `success` tinyint(1) NOT NULL,
  `error_message` text COLLATE utf8mb4_unicode_ci,
  `severity` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `category` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  `created_by_user_id` int DEFAULT NULL,
  `updated_by_user_id` int DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted_by_user_id` int DEFAULT NULL,
  `version` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_audit_logs_action` (`action`),
  KEY `ix_audit_logs_entity_id` (`entity_id`),
  KEY `ix_audit_logs_entity_type` (`entity_type`),
  KEY `ix_audit_logs_ip_address` (`ip_address`),
  KEY `ix_audit_logs_request_id` (`request_id`),
  KEY `ix_audit_logs_session_id` (`session_id`),
  KEY `ix_audit_logs_user_id` (`user_id`),
  CONSTRAINT `fk_audit_logs_user_id_users` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=35 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO `audit_logs` (user_id, session_id, ip_address, user_agent, request_id, action, entity_type, entity_id, entity_repr, old_values, new_values, changed_fields, success, error_message, severity, category, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "2b9591ab1ce4e568317e8f0a67121313514755c0a4b600da29197dbd6f4d9d5d", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", NULL, "login", "user", 1, "admin", "null", "null", "null", 1, NULL, "info", "auth", 1, datetime.datetime(2026, 11, 16, 6, 42, 48), datetime.datetime(2026, 11, 16, 6, 42, 48), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `audit_logs` (user_id, session_id, ip_address, user_agent, request_id, action, entity_type, entity_id, entity_repr, old_values, new_values, changed_fields, success, error_message, severity, category, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "8aa16d46b37d9d08138bc42393cde732ef420624ea5125c15811462320b2d02c", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", NULL, "login", "user", 1, "admin", "null", "null", "null", 0, "invalid_password", "warning", "auth", 2, datetime.datetime(2026, 11, 16, 8, 6, 31), datetime.datetime(2026, 11, 16, 8, 6, 31), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `audit_logs` (user_id, session_id, ip_address, user_agent, request_id, action, entity_type, entity_id, entity_repr, old_values, new_values, changed_fields, success, error_message, severity, category, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "697c21859cc1f88c66673d15a8ba0b8ae805fa0b36e1f134f7669c600449d70b", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", NULL, "login", "user", 1, "admin", "null", "null", "null", 0, "invalid_password", "warning", "auth", 3, datetime.datetime(2026, 11, 16, 8, 6, 42), datetime.datetime(2026, 11, 16, 8, 6, 42), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `audit_logs` (user_id, session_id, ip_address, user_agent, request_id, action, entity_type, entity_id, entity_repr, old_values, new_values, changed_fields, success, error_message, severity, category, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "261ff0d16bf66d82596650db1254bf06107a0819e6efb15ca92d2bf82c702113", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", NULL, "login", "user", 1, "admin", "null", "null", "null", 0, "invalid_password", "warning", "auth", 4, datetime.datetime(2026, 11, 16, 8, 6, 51), datetime.datetime(2026, 11, 16, 8, 6, 51), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `audit_logs` (user_id, session_id, ip_address, user_agent, request_id, action, entity_type, entity_id, entity_repr, old_values, new_values, changed_fields, success, error_message, severity, category, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "acb35e26043ac26cc7e2fe133aa81203c3a799c3ea9e4da2f8fa1e7e12fefaf2", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", NULL, "login", "user", 1, "admin", "null", "null", "null", 0, "invalid_password", "warning", "auth", 5, datetime.datetime(2026, 11, 16, 8, 9, 50), datetime.datetime(2026, 11, 16, 8, 9, 50), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `audit_logs` (user_id, session_id, ip_address, user_agent, request_id, action, entity_type, entity_id, entity_repr, old_values, new_values, changed_fields, success, error_message, severity, category, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "c4cddb66c58a1b384f075765da15d17cead64d539fe6523432e880565e78abd2", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", NULL, "login", "user", 1, "admin", "null", "null", "null", 0, "account_locked", "warning", "auth", 6, datetime.datetime(2026, 11, 16, 8, 11, 23), datetime.datetime(2026, 11, 16, 8, 11, 23), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `audit_logs` (user_id, session_id, ip_address, user_agent, request_id, action, entity_type, entity_id, entity_repr, old_values, new_values, changed_fields, success, error_message, severity, category, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "f52940d79942d637dab44c60c64a75cf7c8b1ff3fcc698c0d9e1e7ab31325ff0", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", NULL, "login", "user", 1, "admin", "null", "null", "null", 0, "account_locked", "warning", "auth", 7, datetime.datetime(2026, 11, 16, 8, 12, 5), datetime.datetime(2026, 11, 16, 8, 12, 5), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `audit_logs` (user_id, session_id, ip_address, user_agent, request_id, action, entity_type, entity_id, entity_repr, old_values, new_values, changed_fields, success, error_message, severity, category, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "09e6f454009804c291170db5e0104f7dce931074a88f4e95bb74bc9000f448fd", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", NULL, "login", "user", 1, "admin", "null", "null", "null", 1, NULL, "info", "auth", 8, datetime.datetime(2026, 11, 16, 8, 12, 27), datetime.datetime(2026, 11, 16, 8, 12, 27), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `audit_logs` (user_id, session_id, ip_address, user_agent, request_id, action, entity_type, entity_id, entity_repr, old_values, new_values, changed_fields, success, error_message, severity, category, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "34ba6d7721e847fcad33d6725e07f14a332949332baac45cc01eb437633b4dd5", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", NULL, "create_complaint", "complaint", 7, "ITC-2026-000001", "null", "{\"title\": \"test\", \"status\": \"New\", \"priority\": \"Critical\", \"complaint_number\": \"ITC-2026-000001\"}", "null", 1, NULL, "info", "data", 9, datetime.datetime(2026, 11, 16, 8, 41, 16), datetime.datetime(2026, 11, 16, 8, 41, 16), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `audit_logs` (user_id, session_id, ip_address, user_agent, request_id, action, entity_type, entity_id, entity_repr, old_values, new_values, changed_fields, success, error_message, severity, category, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (NULL, "6fed4ab1a5343e985b293e547e34f578501ccc45fd3bebf8e1d64fe915fed1e7", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", NULL, "login", "user", NULL, "agent", "null", "null", "null", 0, "user_not_found", "warning", "auth", 10, datetime.datetime(2026, 11, 16, 8, 41, 33), datetime.datetime(2026, 11, 16, 8, 41, 33), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `audit_logs` (user_id, session_id, ip_address, user_agent, request_id, action, entity_type, entity_id, entity_repr, old_values, new_values, changed_fields, success, error_message, severity, category, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (3, "44a85d8a223baaf9125babacfddc675ff935f27fcdec6a4000d1077bbdc3b75f", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", NULL, "login", "user", 3, "support", "null", "null", "null", 1, NULL, "info", "auth", 11, datetime.datetime(2026, 11, 16, 8, 41, 52), datetime.datetime(2026, 11, 16, 8, 41, 52), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `audit_logs` (user_id, session_id, ip_address, user_agent, request_id, action, entity_type, entity_id, entity_repr, old_values, new_values, changed_fields, success, error_message, severity, category, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "566aaae5a7e1d7bf1af6ab2ed04147ddb5c6ae754f519ebeb1af51f2fdbfaf75", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", NULL, "create_complaint", "complaint", 8, "ITC-2026-000002", "null", "{\"title\": \"test2\", \"status\": \"New\", \"priority\": \"Critical\", \"complaint_number\": \"ITC-2026-000002\"}", "null", 1, NULL, "info", "data", 12, datetime.datetime(2026, 11, 16, 8, 42, 32), datetime.datetime(2026, 11, 16, 8, 42, 32), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `audit_logs` (user_id, session_id, ip_address, user_agent, request_id, action, entity_type, entity_id, entity_repr, old_values, new_values, changed_fields, success, error_message, severity, category, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (6, "25e831b5fdc64c4bc0cd7177a3d5a1734eb6ff134069d954b9f5f5384ddcadaf", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", NULL, "login", "user", 6, "demo_support", "null", "null", "null", 0, "invalid_password", "warning", "auth", 13, datetime.datetime(2026, 11, 16, 8, 43, 33), datetime.datetime(2026, 11, 16, 8, 43, 33), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `audit_logs` (user_id, session_id, ip_address, user_agent, request_id, action, entity_type, entity_id, entity_repr, old_values, new_values, changed_fields, success, error_message, severity, category, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (6, "05b282447bb00f54d2abb636eb099f8af59aa7d763aef48bee46932fd956934f", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", NULL, "login", "user", 6, "demo_support", "null", "null", "null", 1, NULL, "info", "auth", 14, datetime.datetime(2026, 11, 16, 8, 43, 45), datetime.datetime(2026, 11, 16, 8, 43, 45), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `audit_logs` (user_id, session_id, ip_address, user_agent, request_id, action, entity_type, entity_id, entity_repr, old_values, new_values, changed_fields, success, error_message, severity, category, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "ff76b7902df7c7afe226511ccc1bc192c83d4a49a64be5b219c94c6cf5127ff8", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", NULL, "login", "user", 1, "admin", "null", "null", "null", 0, "invalid_password", "warning", "auth", 15, datetime.datetime(2026, 11, 19, 7, 28, 3), datetime.datetime(2026, 11, 19, 7, 28, 3), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `audit_logs` (user_id, session_id, ip_address, user_agent, request_id, action, entity_type, entity_id, entity_repr, old_values, new_values, changed_fields, success, error_message, severity, category, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "aad8c6f757add74a890878f744ad0e53a74ba6fec105244bd6c4dc6721f1e297", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", NULL, "login", "user", 1, "admin", "null", "null", "null", 0, "invalid_password", "warning", "auth", 16, datetime.datetime(2026, 11, 19, 7, 28, 10), datetime.datetime(2026, 11, 19, 7, 28, 10), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `audit_logs` (user_id, session_id, ip_address, user_agent, request_id, action, entity_type, entity_id, entity_repr, old_values, new_values, changed_fields, success, error_message, severity, category, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "c7935ee2eea216f8dc8d6be6ce2634d023e029f386ee312ce591f1e08faba13b", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", NULL, "login", "user", 1, "admin", "null", "null", "null", 1, NULL, "info", "auth", 17, datetime.datetime(2026, 11, 19, 7, 28, 22), datetime.datetime(2026, 11, 19, 7, 28, 22), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `audit_logs` (user_id, session_id, ip_address, user_agent, request_id, action, entity_type, entity_id, entity_repr, old_values, new_values, changed_fields, success, error_message, severity, category, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (2, "da43600b3b85c868e8c62de31dcde28f1b583f941ea9edfe1fcaafe6d90bcf9e", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", NULL, "login", "user", 2, "helpdesk", "null", "null", "null", 1, NULL, "info", "auth", 18, datetime.datetime(2026, 11, 19, 7, 46, 25), datetime.datetime(2026, 11, 19, 7, 46, 25), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `audit_logs` (user_id, session_id, ip_address, user_agent, request_id, action, entity_type, entity_id, entity_repr, old_values, new_values, changed_fields, success, error_message, severity, category, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (3, "1ee01f7a8e1e87bbf9122a245fba9fddda9296d0b7be7c17c45ff9625161ab2f", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", NULL, "login", "user", 3, "support", "null", "null", "null", 1, NULL, "info", "auth", 19, datetime.datetime(2026, 11, 19, 7, 46, 57), datetime.datetime(2026, 11, 19, 7, 46, 57), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `audit_logs` (user_id, session_id, ip_address, user_agent, request_id, action, entity_type, entity_id, entity_repr, old_values, new_values, changed_fields, success, error_message, severity, category, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (4, "218b249cd6e751b63b36475bfd8a2b79d528c52d94fbdb8f706931e1092ca8e1", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", NULL, "login", "user", 4, "user", "null", "null", "null", 1, NULL, "info", "auth", 20, datetime.datetime(2026, 11, 19, 7, 47, 16), datetime.datetime(2026, 11, 19, 7, 47, 16), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `audit_logs` (user_id, session_id, ip_address, user_agent, request_id, action, entity_type, entity_id, entity_repr, old_values, new_values, changed_fields, success, error_message, severity, category, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "3bd3c0530ad8d839eb125e090fd8265a690df3613cb6e036b0dc7c06d6870180", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", NULL, "login", "user", 1, "admin", "null", "null", "null", 1, NULL, "info", "auth", 21, datetime.datetime(2026, 11, 19, 7, 47, 41), datetime.datetime(2026, 11, 19, 7, 47, 41), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `audit_logs` (user_id, session_id, ip_address, user_agent, request_id, action, entity_type, entity_id, entity_repr, old_values, new_values, changed_fields, success, error_message, severity, category, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (4, "f0431eb6cea946bd71889285234716df3edb0d4a056d987121075c25d75c37fe", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", NULL, "login", "user", 4, "user", "null", "null", "null", 1, NULL, "info", "auth", 22, datetime.datetime(2026, 11, 19, 7, 48, 45), datetime.datetime(2026, 11, 19, 7, 48, 45), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `audit_logs` (user_id, session_id, ip_address, user_agent, request_id, action, entity_type, entity_id, entity_repr, old_values, new_values, changed_fields, success, error_message, severity, category, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (4, "18533cbb22635a0455261db759381710c7c845a0922b7060b092aeeb288d81f2", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", NULL, "create_complaint", "complaint", 9, "ITC-2026-000003", "null", "{\"title\": \"user test\", \"status\": \"New\", \"priority\": \"Critical\", \"complaint_number\": \"ITC-2026-000003\"}", "null", 1, NULL, "info", "data", 23, datetime.datetime(2026, 11, 19, 7, 49, 47), datetime.datetime(2026, 11, 19, 7, 49, 47), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `audit_logs` (user_id, session_id, ip_address, user_agent, request_id, action, entity_type, entity_id, entity_repr, old_values, new_values, changed_fields, success, error_message, severity, category, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (4, "db708d88fc0b391372d755ce22aa10a85b3f7712572d556de95e86cf07fa5387", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", NULL, "login", "user", 4, "user", "null", "null", "null", 1, NULL, "info", "auth", 24, datetime.datetime(2026, 11, 19, 7, 51, 8), datetime.datetime(2026, 11, 19, 7, 51, 8), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `audit_logs` (user_id, session_id, ip_address, user_agent, request_id, action, entity_type, entity_id, entity_repr, old_values, new_values, changed_fields, success, error_message, severity, category, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (4, "40a91bf86a19fd848b8d814fadad929d4046dc40cf69cef2fc637433aec24c35", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", NULL, "login", "user", 4, "user", "null", "null", "null", 0, "invalid_password", "warning", "auth", 25, datetime.datetime(2026, 11, 19, 7, 51, 16), datetime.datetime(2026, 11, 19, 7, 51, 16), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `audit_logs` (user_id, session_id, ip_address, user_agent, request_id, action, entity_type, entity_id, entity_repr, old_values, new_values, changed_fields, success, error_message, severity, category, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (3, "8ee8e4bf1ecd4e372ee9dd3baaa84581e417c75e22993243e7edf56638b3cd7e", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", NULL, "login", "user", 3, "support", "null", "null", "null", 1, NULL, "info", "auth", 26, datetime.datetime(2026, 11, 19, 7, 51, 57), datetime.datetime(2026, 11, 19, 7, 51, 57), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `audit_logs` (user_id, session_id, ip_address, user_agent, request_id, action, entity_type, entity_id, entity_repr, old_values, new_values, changed_fields, success, error_message, severity, category, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (3, "fcb7b3c80641b2bfed19a98cf6c96739c28e95941ac6c766c8e2ee24340e358b", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", NULL, "login", "user", 3, "support", "null", "null", "null", 1, NULL, "info", "auth", 27, datetime.datetime(2026, 11, 19, 7, 52, 9), datetime.datetime(2026, 11, 19, 7, 52, 9), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `audit_logs` (user_id, session_id, ip_address, user_agent, request_id, action, entity_type, entity_id, entity_repr, old_values, new_values, changed_fields, success, error_message, severity, category, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (4, "7271a3bc23112566e8b0e00bfde47124c9d8bcc0447d9d5caba16637cbb936dd", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", NULL, "login", "user", 4, "user", "null", "null", "null", 1, NULL, "info", "auth", 28, datetime.datetime(2026, 11, 19, 7, 53, 29), datetime.datetime(2026, 11, 19, 7, 53, 29), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `audit_logs` (user_id, session_id, ip_address, user_agent, request_id, action, entity_type, entity_id, entity_repr, old_values, new_values, changed_fields, success, error_message, severity, category, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "a79f38440736ee3f6bdb58027675b0dda8b6f7d2ab5dfb5642fb85d0df29db48", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", NULL, "login", "user", 1, "admin", "null", "null", "null", 1, NULL, "info", "auth", 29, datetime.datetime(2026, 11, 19, 9, 9, 29), datetime.datetime(2026, 11, 19, 9, 9, 29), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `audit_logs` (user_id, session_id, ip_address, user_agent, request_id, action, entity_type, entity_id, entity_repr, old_values, new_values, changed_fields, success, error_message, severity, category, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "99e36dd047f1add3b77dce9c42600413f02ed01fdb0fdc3f1b376feed35f6b9a", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", NULL, "login", "user", 1, "admin", "null", "null", "null", 1, NULL, "info", "auth", 30, datetime.datetime(2026, 11, 19, 13, 58, 17), datetime.datetime(2026, 11, 19, 13, 58, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `audit_logs` (user_id, session_id, ip_address, user_agent, request_id, action, entity_type, entity_id, entity_repr, old_values, new_values, changed_fields, success, error_message, severity, category, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "93008b536131af43392da0966d0aca8ef3f1a5bab0a58cc4d9e53da4cc1fb75a", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", NULL, "login", "user", 1, "admin", "null", "null", "null", 1, NULL, "info", "auth", 31, datetime.datetime(2026, 11, 19, 14, 20, 17), datetime.datetime(2026, 11, 19, 14, 20, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `audit_logs` (user_id, session_id, ip_address, user_agent, request_id, action, entity_type, entity_id, entity_repr, old_values, new_values, changed_fields, success, error_message, severity, category, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "b092990748a3f53fa030993d8cd24fa8bd09d2b3d3d4625085f31c3316591206", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Qoder/0.5.5 Chrome/150.0.7871.250 Electron/43.8.4 Safari/537.36", NULL, "login", "user", 1, "admin", "null", "null", "null", 0, "invalid_password", "warning", "auth", 32, datetime.datetime(2026, 11, 19, 14, 48, 10), datetime.datetime(2026, 11, 19, 14, 48, 10), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `audit_logs` (user_id, session_id, ip_address, user_agent, request_id, action, entity_type, entity_id, entity_repr, old_values, new_values, changed_fields, success, error_message, severity, category, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "1e7e82d2bf42ae15c8253776ee1b098f9b0fb4f62e76522f13c1291a45d46757", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Qoder/0.5.5 Chrome/150.0.7871.250 Electron/43.8.4 Safari/537.36", NULL, "login", "user", 1, "admin", "null", "null", "null", 1, NULL, "info", "auth", 33, datetime.datetime(2026, 11, 19, 14, 59, 44), datetime.datetime(2026, 11, 19, 14, 59, 44), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `audit_logs` (user_id, session_id, ip_address, user_agent, request_id, action, entity_type, entity_id, entity_repr, old_values, new_values, changed_fields, success, error_message, severity, category, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "a82390374b0cf5a1a00aa5effb10e9eb56477cc6fbecd145202891c34ca07447", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", NULL, "login", "user", 1, "admin", "null", "null", "null", 1, NULL, "info", "auth", 34, datetime.datetime(2026, 11, 19, 15, 3, 47), datetime.datetime(2026, 11, 19, 15, 3, 47), NULL, NULL, 1, NULL, NULL, 1);
-- Table: categories
-- Row count: 7
CREATE TABLE `categories` (
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `parent_id` int DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `sort_order` int NOT NULL,
  `department_id` int DEFAULT NULL,
  `auto_assign_to_id` int DEFAULT NULL,
  `requires_asset` tinyint(1) NOT NULL,
  `default_sla_policy_id` int DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  `created_by_user_id` int DEFAULT NULL,
  `updated_by_user_id` int DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted_by_user_id` int DEFAULT NULL,
  `version` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_categories_code` (`code`),
  UNIQUE KEY `ix_categories_name` (`name`),
  KEY `fk_categories_auto_assign_to_id_users` (`auto_assign_to_id`),
  KEY `fk_categories_default_sla` (`default_sla_policy_id`),
  KEY `fk_categories_department_id_departments` (`department_id`),
  KEY `fk_categories_parent_id_categories` (`parent_id`),
  CONSTRAINT `fk_categories_auto_assign_to_id_users` FOREIGN KEY (`auto_assign_to_id`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_categories_default_sla` FOREIGN KEY (`default_sla_policy_id`) REFERENCES `sla_policies` (`id`),
  CONSTRAINT `fk_categories_department_id_departments` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`),
  CONSTRAINT `fk_categories_parent_id_categories` FOREIGN KEY (`parent_id`) REFERENCES `categories` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO `categories` (name, code, description, parent_id, is_active, sort_order, department_id, auto_assign_to_id, requires_asset, default_sla_policy_id, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id, version) VALUES ("Hardware", "HARDWARE", "Computers, printers, peripherals", NULL, 1, 0, NULL, NULL, 0, NULL, 1, datetime.datetime(2026, 11, 16, 6, 40, 18), datetime.datetime(2026, 11, 16, 6, 40, 18), NULL, NULL, NULL, NULL, 1);
INSERT INTO `categories` (name, code, description, parent_id, is_active, sort_order, department_id, auto_assign_to_id, requires_asset, default_sla_policy_id, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id, version) VALUES ("Software", "SOFTWARE", "Applications and licenses", NULL, 1, 0, NULL, NULL, 0, NULL, 2, datetime.datetime(2026, 11, 16, 6, 40, 18), datetime.datetime(2026, 11, 16, 6, 40, 18), NULL, NULL, NULL, NULL, 1);
INSERT INTO `categories` (name, code, description, parent_id, is_active, sort_order, department_id, auto_assign_to_id, requires_asset, default_sla_policy_id, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id, version) VALUES ("Network", "NETWORK", "Connectivity, Wi-Fi, VPN", NULL, 1, 0, NULL, NULL, 0, NULL, 3, datetime.datetime(2026, 11, 16, 6, 40, 18), datetime.datetime(2026, 11, 16, 6, 40, 18), NULL, NULL, NULL, NULL, 1);
INSERT INTO `categories` (name, code, description, parent_id, is_active, sort_order, department_id, auto_assign_to_id, requires_asset, default_sla_policy_id, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id, version) VALUES ("Access & Accounts", "ACCESS", "Accounts, passwords and permissions", NULL, 1, 0, NULL, NULL, 0, NULL, 4, datetime.datetime(2026, 11, 16, 6, 40, 18), datetime.datetime(2026, 11, 16, 6, 40, 18), NULL, NULL, NULL, NULL, 1);
INSERT INTO `categories` (name, code, description, parent_id, is_active, sort_order, department_id, auto_assign_to_id, requires_asset, default_sla_policy_id, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id, version) VALUES ("Printing", "PRINTING", "Printers and print queues", NULL, 1, 0, NULL, NULL, 0, NULL, 5, datetime.datetime(2026, 11, 16, 6, 40, 18), datetime.datetime(2026, 11, 16, 6, 40, 18), NULL, NULL, NULL, NULL, 1);
INSERT INTO `categories` (name, code, description, parent_id, is_active, sort_order, department_id, auto_assign_to_id, requires_asset, default_sla_policy_id, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id, version) VALUES ("Clinical Application", "CLINICAL", "Clinical system issues", NULL, 1, 0, NULL, NULL, 0, NULL, 6, datetime.datetime(2026, 11, 16, 6, 40, 18), datetime.datetime(2026, 11, 16, 6, 40, 18), NULL, NULL, NULL, NULL, 1);
INSERT INTO `categories` (name, code, description, parent_id, is_active, sort_order, department_id, auto_assign_to_id, requires_asset, default_sla_policy_id, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id, version) VALUES ("Other", "OTHER", "Anything else", NULL, 1, 0, NULL, NULL, 0, NULL, 7, datetime.datetime(2026, 11, 16, 6, 40, 18), datetime.datetime(2026, 11, 16, 6, 40, 18), NULL, NULL, NULL, NULL, 1);
-- Table: comments
-- Row count: 0
CREATE TABLE `comments` (
  `complaint_id` int NOT NULL,
  `user_id` int NOT NULL,
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `visibility` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_system` tinyint(1) NOT NULL,
  `parent_id` int DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  `created_by_user_id` int DEFAULT NULL,
  `updated_by_user_id` int DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted_by_user_id` int DEFAULT NULL,
  `version` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_comments_complaint_id` (`complaint_id`),
  KEY `fk_comments_parent_id_comments` (`parent_id`),
  KEY `fk_comments_user_id_users` (`user_id`),
  CONSTRAINT `fk_comments_complaint_id_complaints` FOREIGN KEY (`complaint_id`) REFERENCES `complaints` (`id`),
  CONSTRAINT `fk_comments_parent_id_comments` FOREIGN KEY (`parent_id`) REFERENCES `comments` (`id`),
  CONSTRAINT `fk_comments_user_id_users` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
-- Table: complaint_assignments
-- Row count: 3
CREATE TABLE `complaint_assignments` (
  `complaint_id` int NOT NULL,
  `previous_assignee_id` int DEFAULT NULL,
  `new_assignee_id` int NOT NULL,
  `assigned_by_user_id` int NOT NULL,
  `assignment_reason` text COLLATE utf8mb4_unicode_ci,
  `notes` text COLLATE utf8mb4_unicode_ci,
  `assigned_at` datetime NOT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  `created_by_user_id` int DEFAULT NULL,
  `updated_by_user_id` int DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted_by_user_id` int DEFAULT NULL,
  `version` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_complaint_assignments_assigned_at` (`assigned_at`),
  KEY `ix_complaint_assignments_complaint_id` (`complaint_id`),
  KEY `ix_complaint_assignments_new_assignee_id` (`new_assignee_id`),
  KEY `fk_complaint_assignments_assigned_by_user_id_users` (`assigned_by_user_id`),
  KEY `fk_complaint_assignments_previous_assignee_id_users` (`previous_assignee_id`),
  CONSTRAINT `fk_complaint_assignments_assigned_by_user_id_users` FOREIGN KEY (`assigned_by_user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_complaint_assignments_complaint_id_complaints` FOREIGN KEY (`complaint_id`) REFERENCES `complaints` (`id`),
  CONSTRAINT `fk_complaint_assignments_new_assignee_id_users` FOREIGN KEY (`new_assignee_id`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_complaint_assignments_previous_assignee_id_users` FOREIGN KEY (`previous_assignee_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO `complaint_assignments` (complaint_id, previous_assignee_id, new_assignee_id, assigned_by_user_id, assignment_reason, notes, assigned_at, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (7, NULL, 3, 1, NULL, NULL, datetime.datetime(2026, 11, 16, 8, 41, 15), 1, datetime.datetime(2026, 11, 16, 8, 41, 15), datetime.datetime(2026, 11, 16, 8, 41, 15), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `complaint_assignments` (complaint_id, previous_assignee_id, new_assignee_id, assigned_by_user_id, assignment_reason, notes, assigned_at, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (8, NULL, 6, 1, NULL, NULL, datetime.datetime(2026, 11, 16, 8, 42, 32), 2, datetime.datetime(2026, 11, 16, 8, 42, 32), datetime.datetime(2026, 11, 16, 8, 42, 32), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `complaint_assignments` (complaint_id, previous_assignee_id, new_assignee_id, assigned_by_user_id, assignment_reason, notes, assigned_at, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (9, NULL, 3, 4, NULL, NULL, datetime.datetime(2026, 11, 19, 7, 49, 47), 3, datetime.datetime(2026, 11, 19, 7, 49, 47), datetime.datetime(2026, 11, 19, 7, 49, 47), NULL, NULL, 1, NULL, NULL, 1);
-- Table: complaint_history
-- Row count: 3
CREATE TABLE `complaint_history` (
  `complaint_id` int NOT NULL,
  `user_id` int NOT NULL,
  `action` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `field_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `old_value` text COLLATE utf8mb4_unicode_ci,
  `new_value` text COLLATE utf8mb4_unicode_ci,
  `description` text COLLATE utf8mb4_unicode_ci,
  `ip_address` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `user_agent` text COLLATE utf8mb4_unicode_ci,
  `created_at` datetime NOT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `updated_at` datetime NOT NULL,
  `created_by_user_id` int DEFAULT NULL,
  `updated_by_user_id` int DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted_by_user_id` int DEFAULT NULL,
  `version` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_complaint_history_action` (`action`),
  KEY `ix_complaint_history_complaint_id` (`complaint_id`),
  KEY `ix_complaint_history_created_at` (`created_at`),
  KEY `fk_complaint_history_user_id_users` (`user_id`),
  CONSTRAINT `fk_complaint_history_complaint_id_complaints` FOREIGN KEY (`complaint_id`) REFERENCES `complaints` (`id`),
  CONSTRAINT `fk_complaint_history_user_id_users` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO `complaint_history` (complaint_id, user_id, action, field_name, old_value, new_value, description, ip_address, user_agent, created_at, id, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (7, 1, "created", NULL, NULL, NULL, "Complaint created with status New", NULL, NULL, datetime.datetime(2026, 11, 16, 8, 41, 15), 1, datetime.datetime(2026, 11, 16, 8, 41, 15), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `complaint_history` (complaint_id, user_id, action, field_name, old_value, new_value, description, ip_address, user_agent, created_at, id, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (8, 1, "created", NULL, NULL, NULL, "Complaint created with status New", NULL, NULL, datetime.datetime(2026, 11, 16, 8, 42, 32), 2, datetime.datetime(2026, 11, 16, 8, 42, 32), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `complaint_history` (complaint_id, user_id, action, field_name, old_value, new_value, description, ip_address, user_agent, created_at, id, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (9, 4, "created", NULL, NULL, NULL, "Complaint created with status New", NULL, NULL, datetime.datetime(2026, 11, 19, 7, 49, 47), 3, datetime.datetime(2026, 11, 19, 7, 49, 47), NULL, NULL, 1, NULL, NULL, 1);
-- Table: complaint_number_sequences
-- Row count: 1
CREATE TABLE `complaint_number_sequences` (
  `year` int NOT NULL AUTO_INCREMENT,
  `next_number` int NOT NULL DEFAULT '1',
  PRIMARY KEY (`year`)
) ENGINE=InnoDB AUTO_INCREMENT=2027 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO `complaint_number_sequences` (year, next_number) VALUES (2026, 4);
-- Table: complaint_status_history
-- Row count: 3
CREATE TABLE `complaint_status_history` (
  `complaint_id` int NOT NULL,
  `from_status_id` int DEFAULT NULL,
  `to_status_id` int NOT NULL,
  `changed_by_user_id` int NOT NULL,
  `reason` text COLLATE utf8mb4_unicode_ci,
  `notes` text COLLATE utf8mb4_unicode_ci,
  `changed_at` datetime NOT NULL,
  `sla_paused` tinyint(1) NOT NULL,
  `sla_resumed` tinyint(1) NOT NULL,
  `sla_adjustment_reason` text COLLATE utf8mb4_unicode_ci,
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  `created_by_user_id` int DEFAULT NULL,
  `updated_by_user_id` int DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted_by_user_id` int DEFAULT NULL,
  `version` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_complaint_status_history_changed_at` (`changed_at`),
  KEY `ix_complaint_status_history_complaint_id` (`complaint_id`),
  KEY `ix_complaint_status_history_to_status_id` (`to_status_id`),
  KEY `fk_complaint_status_history_changed_by_user_id_users` (`changed_by_user_id`),
  KEY `fk_complaint_status_history_from_status_id_statuses` (`from_status_id`),
  CONSTRAINT `fk_complaint_status_history_changed_by_user_id_users` FOREIGN KEY (`changed_by_user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_complaint_status_history_complaint_id_complaints` FOREIGN KEY (`complaint_id`) REFERENCES `complaints` (`id`),
  CONSTRAINT `fk_complaint_status_history_from_status_id_statuses` FOREIGN KEY (`from_status_id`) REFERENCES `statuses` (`id`),
  CONSTRAINT `fk_complaint_status_history_to_status_id_statuses` FOREIGN KEY (`to_status_id`) REFERENCES `statuses` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO `complaint_status_history` (complaint_id, from_status_id, to_status_id, changed_by_user_id, reason, notes, changed_at, sla_paused, sla_resumed, sla_adjustment_reason, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (7, NULL, 1, 1, "Complaint created", NULL, datetime.datetime(2026, 11, 16, 8, 41, 15), 0, 0, NULL, 1, datetime.datetime(2026, 11, 16, 8, 41, 15), datetime.datetime(2026, 11, 16, 8, 41, 15), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `complaint_status_history` (complaint_id, from_status_id, to_status_id, changed_by_user_id, reason, notes, changed_at, sla_paused, sla_resumed, sla_adjustment_reason, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (8, NULL, 1, 1, "Complaint created", NULL, datetime.datetime(2026, 11, 16, 8, 42, 32), 0, 0, NULL, 2, datetime.datetime(2026, 11, 16, 8, 42, 32), datetime.datetime(2026, 11, 16, 8, 42, 32), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `complaint_status_history` (complaint_id, from_status_id, to_status_id, changed_by_user_id, reason, notes, changed_at, sla_paused, sla_resumed, sla_adjustment_reason, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (9, NULL, 1, 4, "Complaint created", NULL, datetime.datetime(2026, 11, 19, 7, 49, 47), 0, 0, NULL, 3, datetime.datetime(2026, 11, 19, 7, 49, 47), datetime.datetime(2026, 11, 19, 7, 49, 47), NULL, NULL, 1, NULL, NULL, 1);
-- Table: complaints
-- Row count: 9
CREATE TABLE `complaints` (
  `complaint_number` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `title` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `category_id` int NOT NULL,
  `priority_id` int NOT NULL,
  `status_id` int NOT NULL,
  `department_id` int NOT NULL,
  `software_id` int NOT NULL,
  `affected_location` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `affected_device` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `ward_or_location` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `affected_users_count` int NOT NULL,
  `reported_by_user_id` int NOT NULL,
  `reporter_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `reporter_employee_number` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `reporter_department` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `reporter_extension` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `reporter_contact` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `reporter_patient_mrn` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_by_user_id` int NOT NULL,
  `assigned_to_user_id` int DEFAULT NULL,
  `source_type` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `source_reference` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `severity` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `assignment_notes` text COLLATE utf8mb4_unicode_ci,
  `resolution_summary` text COLLATE utf8mb4_unicode_ci,
  `root_cause` text COLLATE utf8mb4_unicode_ci,
  `workaround` text COLLATE utf8mb4_unicode_ci,
  `resolved_by_user_id` int DEFAULT NULL,
  `incident_started_at` datetime DEFAULT NULL,
  `first_response_at` datetime DEFAULT NULL,
  `assigned_at` datetime DEFAULT NULL,
  `resolved_at` datetime DEFAULT NULL,
  `closed_at` datetime DEFAULT NULL,
  `sla_response_deadline` datetime DEFAULT NULL,
  `sla_resolution_deadline` datetime DEFAULT NULL,
  `is_confidential` tinyint(1) NOT NULL,
  `is_escalated` tinyint(1) NOT NULL,
  `escalated_at` datetime DEFAULT NULL,
  `escalated_to_user_id` int DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  `updated_by_user_id` int DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted_by_user_id` int DEFAULT NULL,
  `version` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_complaints_complaint_number` (`complaint_number`),
  KEY `ix_complaints_assigned_to_user_id` (`assigned_to_user_id`),
  KEY `ix_complaints_category_id` (`category_id`),
  KEY `ix_complaints_closed_at` (`closed_at`),
  KEY `ix_complaints_created_by_user_id` (`created_by_user_id`),
  KEY `ix_complaints_department_id` (`department_id`),
  KEY `ix_complaints_incident_started_at` (`incident_started_at`),
  KEY `ix_complaints_priority_id` (`priority_id`),
  KEY `ix_complaints_reported_by_user_id` (`reported_by_user_id`),
  KEY `ix_complaints_resolved_at` (`resolved_at`),
  KEY `ix_complaints_severity` (`severity`),
  KEY `ix_complaints_sla_resolution_deadline` (`sla_resolution_deadline`),
  KEY `ix_complaints_sla_response_deadline` (`sla_response_deadline`),
  KEY `ix_complaints_software_id` (`software_id`),
  KEY `ix_complaints_status_id` (`status_id`),
  KEY `fk_complaints_escalated_to_user_id_users` (`escalated_to_user_id`),
  KEY `fk_complaints_resolved_by_user_id_users` (`resolved_by_user_id`),
  CONSTRAINT `fk_complaints_assigned_to_user_id_users` FOREIGN KEY (`assigned_to_user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_complaints_category_id_categories` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`),
  CONSTRAINT `fk_complaints_created_by_user_id_users` FOREIGN KEY (`created_by_user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_complaints_department_id_departments` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`),
  CONSTRAINT `fk_complaints_escalated_to_user_id_users` FOREIGN KEY (`escalated_to_user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_complaints_priority_id_priorities` FOREIGN KEY (`priority_id`) REFERENCES `priorities` (`id`),
  CONSTRAINT `fk_complaints_reported_by_user_id_users` FOREIGN KEY (`reported_by_user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_complaints_resolved_by_user_id_users` FOREIGN KEY (`resolved_by_user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_complaints_software_id_software_catalog` FOREIGN KEY (`software_id`) REFERENCES `software_catalog` (`id`),
  CONSTRAINT `fk_complaints_status_id_statuses` FOREIGN KEY (`status_id`) REFERENCES `statuses` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO `complaints` (complaint_number, title, description, category_id, priority_id, status_id, department_id, software_id, affected_location, affected_device, ward_or_location, affected_users_count, reported_by_user_id, reporter_name, reporter_employee_number, reporter_department, reporter_extension, reporter_contact, reporter_patient_mrn, created_by_user_id, assigned_to_user_id, source_type, source_reference, severity, assignment_notes, resolution_summary, root_cause, workaround, resolved_by_user_id, incident_started_at, first_response_at, assigned_at, resolved_at, closed_at, sla_response_deadline, sla_resolution_deadline, is_confidential, is_escalated, escalated_at, escalated_to_user_id, id, created_at, updated_at, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("DEV-2026-0001", "Demo: HIS login problem", "Fictional training complaint: user cannot sign in to HIS.", 2, 2, 1, 1, 1, NULL, NULL, NULL, 1, 4, NULL, NULL, NULL, NULL, NULL, NULL, 4, 2, "portal", NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0, 0, NULL, NULL, 1, datetime.datetime(2026, 11, 16, 6, 40, 18), datetime.datetime(2026, 11, 16, 6, 40, 18), NULL, 1, NULL, NULL, 1);
INSERT INTO `complaints` (complaint_number, title, description, category_id, priority_id, status_id, department_id, software_id, affected_location, affected_device, ward_or_location, affected_users_count, reported_by_user_id, reporter_name, reporter_employee_number, reporter_department, reporter_extension, reporter_contact, reporter_patient_mrn, created_by_user_id, assigned_to_user_id, source_type, source_reference, severity, assignment_notes, resolution_summary, root_cause, workaround, resolved_by_user_id, incident_started_at, first_response_at, assigned_at, resolved_at, closed_at, sla_response_deadline, sla_resolution_deadline, is_confidential, is_escalated, escalated_at, escalated_to_user_id, id, created_at, updated_at, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("DEV-2026-0002", "Demo: Printer not responding", "Fictional training complaint: department printer is offline.", 5, 3, 3, 1, 1, NULL, NULL, NULL, 1, 4, NULL, NULL, NULL, NULL, NULL, NULL, 4, 3, "portal", NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0, 0, NULL, NULL, 2, datetime.datetime(2026, 11, 16, 6, 40, 18), datetime.datetime(2026, 11, 16, 6, 40, 18), NULL, 1, NULL, NULL, 1);
INSERT INTO `complaints` (complaint_number, title, description, category_id, priority_id, status_id, department_id, software_id, affected_location, affected_device, ward_or_location, affected_users_count, reported_by_user_id, reporter_name, reporter_employee_number, reporter_department, reporter_extension, reporter_contact, reporter_patient_mrn, created_by_user_id, assigned_to_user_id, source_type, source_reference, severity, assignment_notes, resolution_summary, root_cause, workaround, resolved_by_user_id, incident_started_at, first_response_at, assigned_at, resolved_at, closed_at, sla_response_deadline, sla_resolution_deadline, is_confidential, is_escalated, escalated_at, escalated_to_user_id, id, created_at, updated_at, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("DEV-2026-0003", "Demo: Network connectivity", "Fictional training complaint: workstation connection is unstable.", 3, 4, 2, 1, 7, NULL, NULL, NULL, 1, 1, NULL, NULL, NULL, NULL, NULL, NULL, 1, 2, "portal", NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0, 0, NULL, NULL, 3, datetime.datetime(2026, 11, 16, 6, 40, 18), datetime.datetime(2026, 11, 16, 6, 40, 18), NULL, 1, NULL, NULL, 1);
INSERT INTO `complaints` (complaint_number, title, description, category_id, priority_id, status_id, department_id, software_id, affected_location, affected_device, ward_or_location, affected_users_count, reported_by_user_id, reporter_name, reporter_employee_number, reporter_department, reporter_extension, reporter_contact, reporter_patient_mrn, created_by_user_id, assigned_to_user_id, source_type, source_reference, severity, assignment_notes, resolution_summary, root_cause, workaround, resolved_by_user_id, incident_started_at, first_response_at, assigned_at, resolved_at, closed_at, sla_response_deadline, sla_resolution_deadline, is_confidential, is_escalated, escalated_at, escalated_to_user_id, id, created_at, updated_at, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("HD-DEMO-0001", "HIS login is slow", "Users report slow login to the training HIS.", 2, 2, 3, 1, 1, "Demo Ward / Outpatient", NULL, NULL, 1, 7, NULL, NULL, NULL, NULL, NULL, NULL, 1, 5, "portal", NULL, "High", NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0, 0, NULL, NULL, 4, datetime.datetime(2026, 11, 16, 6, 59, 1), datetime.datetime(2026, 11, 16, 6, 59, 1), NULL, 1, NULL, NULL, 1);
INSERT INTO `complaints` (complaint_number, title, description, category_id, priority_id, status_id, department_id, software_id, affected_location, affected_device, ward_or_location, affected_users_count, reported_by_user_id, reporter_name, reporter_employee_number, reporter_department, reporter_extension, reporter_contact, reporter_patient_mrn, created_by_user_id, assigned_to_user_id, source_type, source_reference, severity, assignment_notes, resolution_summary, root_cause, workaround, resolved_by_user_id, incident_started_at, first_response_at, assigned_at, resolved_at, closed_at, sla_response_deadline, sla_resolution_deadline, is_confidential, is_escalated, escalated_at, escalated_to_user_id, id, created_at, updated_at, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("HD-DEMO-0002", "Ward printer is offline", "The ward printer is not responding.", 5, 3, 1, 1, 1, "Demo Ward / Outpatient", NULL, NULL, 1, 7, NULL, NULL, NULL, NULL, NULL, NULL, 1, NULL, "phone", NULL, "Medium", NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0, 0, NULL, NULL, 5, datetime.datetime(2026, 11, 16, 6, 59, 1), datetime.datetime(2026, 11, 16, 6, 59, 1), NULL, 1, NULL, NULL, 1);
INSERT INTO `complaints` (complaint_number, title, description, category_id, priority_id, status_id, department_id, software_id, affected_location, affected_device, ward_or_location, affected_users_count, reported_by_user_id, reporter_name, reporter_employee_number, reporter_department, reporter_extension, reporter_contact, reporter_patient_mrn, created_by_user_id, assigned_to_user_id, source_type, source_reference, severity, assignment_notes, resolution_summary, root_cause, workaround, resolved_by_user_id, incident_started_at, first_response_at, assigned_at, resolved_at, closed_at, sla_response_deadline, sla_resolution_deadline, is_confidential, is_escalated, escalated_at, escalated_to_user_id, id, created_at, updated_at, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("HD-DEMO-0003", "Wi-Fi drops intermittently", "Connectivity drops in the outpatient area.", 3, 4, 2, 1, 8, "Demo Ward / Outpatient", NULL, NULL, 1, 7, NULL, NULL, NULL, NULL, NULL, NULL, 1, 6, "walk_in", NULL, "Low", NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0, 0, NULL, NULL, 6, datetime.datetime(2026, 11, 16, 6, 59, 1), datetime.datetime(2026, 11, 16, 6, 59, 1), NULL, 1, NULL, NULL, 1);
INSERT INTO `complaints` (complaint_number, title, description, category_id, priority_id, status_id, department_id, software_id, affected_location, affected_device, ward_or_location, affected_users_count, reported_by_user_id, reporter_name, reporter_employee_number, reporter_department, reporter_extension, reporter_contact, reporter_patient_mrn, created_by_user_id, assigned_to_user_id, source_type, source_reference, severity, assignment_notes, resolution_summary, root_cause, workaround, resolved_by_user_id, incident_started_at, first_response_at, assigned_at, resolved_at, closed_at, sla_response_deadline, sla_resolution_deadline, is_confidential, is_escalated, escalated_at, escalated_to_user_id, id, created_at, updated_at, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("ITC-2026-000001", "test", "testasdfasdfasdf", 6, 1, 1, 5, 6, "RAdio", "pc3511", NULL, 1, 1, NULL, NULL, NULL, NULL, NULL, NULL, 1, 3, "email", NULL, "Critical", NULL, NULL, NULL, NULL, NULL, datetime.datetime(2026, 11, 16, 13, 41), NULL, datetime.datetime(2026, 11, 16, 8, 41, 15), NULL, NULL, datetime.datetime(2026, 11, 16, 10, 0), datetime.datetime(2026, 11, 16, 13, 0), 0, 0, NULL, NULL, 7, datetime.datetime(2026, 11, 16, 8, 41, 15), datetime.datetime(2026, 11, 16, 8, 41, 15), NULL, 1, NULL, NULL, 1);
INSERT INTO `complaints` (complaint_number, title, description, category_id, priority_id, status_id, department_id, software_id, affected_location, affected_device, ward_or_location, affected_users_count, reported_by_user_id, reporter_name, reporter_employee_number, reporter_department, reporter_extension, reporter_contact, reporter_patient_mrn, created_by_user_id, assigned_to_user_id, source_type, source_reference, severity, assignment_notes, resolution_summary, root_cause, workaround, resolved_by_user_id, incident_started_at, first_response_at, assigned_at, resolved_at, closed_at, sla_response_deadline, sla_resolution_deadline, is_confidential, is_escalated, escalated_at, escalated_to_user_id, id, created_at, updated_at, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("ITC-2026-000002", "test2", "asdfasdf asd fas dfa sdf", 4, 1, 1, 3, 7, "azeem", "pc-3511", NULL, 1, 1, NULL, NULL, NULL, NULL, NULL, NULL, 1, 6, "phone", NULL, "Critical", NULL, NULL, NULL, NULL, NULL, datetime.datetime(2026, 11, 16, 13, 42), NULL, datetime.datetime(2026, 11, 16, 8, 42, 32), NULL, NULL, datetime.datetime(2026, 11, 16, 10, 0), datetime.datetime(2026, 11, 16, 13, 0), 0, 0, NULL, NULL, 8, datetime.datetime(2026, 11, 16, 8, 42, 32), datetime.datetime(2026, 11, 16, 8, 42, 32), NULL, 1, NULL, NULL, 1);
INSERT INTO `complaints` (complaint_number, title, description, category_id, priority_id, status_id, department_id, software_id, affected_location, affected_device, ward_or_location, affected_users_count, reported_by_user_id, reporter_name, reporter_employee_number, reporter_department, reporter_extension, reporter_contact, reporter_patient_mrn, created_by_user_id, assigned_to_user_id, source_type, source_reference, severity, assignment_notes, resolution_summary, root_cause, workaround, resolved_by_user_id, incident_started_at, first_response_at, assigned_at, resolved_at, closed_at, sla_response_deadline, sla_resolution_deadline, is_confidential, is_escalated, escalated_at, escalated_to_user_id, id, created_at, updated_at, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("ITC-2026-000003", "user test", "adfasdfsadfasdf", 6, 1, 1, 5, 8, "billing", "pc-3512", NULL, 1, 4, NULL, NULL, NULL, NULL, NULL, NULL, 4, 3, "", NULL, NULL, NULL, NULL, NULL, NULL, NULL, datetime.datetime(2026, 11, 19, 12, 49), NULL, datetime.datetime(2026, 11, 19, 7, 49, 47), NULL, NULL, datetime.datetime(2026, 11, 19, 10, 0), datetime.datetime(2026, 11, 19, 13, 0), 0, 0, NULL, NULL, 9, datetime.datetime(2026, 11, 19, 7, 49, 47), datetime.datetime(2026, 11, 19, 7, 49, 47), NULL, 1, NULL, NULL, 1);
-- Table: departments
-- Row count: 5
CREATE TABLE `departments` (
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `location` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `phone` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `email` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `manager_id` int DEFAULT NULL,
  `sort_order` int NOT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  `created_by_user_id` int DEFAULT NULL,
  `updated_by_user_id` int DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted_by_user_id` int DEFAULT NULL,
  `version` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_departments_code` (`code`),
  UNIQUE KEY `ix_departments_name` (`name`),
  KEY `fk_departments_manager` (`manager_id`),
  CONSTRAINT `fk_departments_manager` FOREIGN KEY (`manager_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO `departments` (name, code, description, location, phone, email, manager_id, sort_order, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("IT Helpdesk", "IT", "First-line IT support", "Ground Floor, Building A", NULL, NULL, NULL, 0, 1, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `departments` (name, code, description, location, phone, email, manager_id, sort_order, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("Network Operations", "NET", "Network and connectivity team", "Basement, Building A", NULL, NULL, NULL, 0, 2, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `departments` (name, code, description, location, phone, email, manager_id, sort_order, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("Clinical Systems", "CLN", "HIS, LIS, PACS and clinical applications", "Second Floor, Building B", NULL, NULL, NULL, 0, 3, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `departments` (name, code, description, location, phone, email, manager_id, sort_order, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("Patient Administration", "PAT", "Admissions, records and patient portal", "First Floor, Building B", NULL, NULL, NULL, 0, 4, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `departments` (name, code, description, location, phone, email, manager_id, sort_order, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("Billing", "BIL", "Billing and finance systems", "Third Floor, Building A", NULL, NULL, NULL, 0, 5, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
-- Table: holidays
-- Row count: 0
CREATE TABLE `holidays` (
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `date` date NOT NULL,
  `is_recurring` tinyint(1) NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `is_active` tinyint(1) NOT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  `created_by_user_id` int DEFAULT NULL,
  `updated_by_user_id` int DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted_by_user_id` int DEFAULT NULL,
  `version` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_holidays_date` (`date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
-- Table: login_attempts
-- Row count: 31
CREATE TABLE `login_attempts` (
  `user_id` int DEFAULT NULL,
  `username_attempted` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ip_address` varchar(45) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_agent` text COLLATE utf8mb4_unicode_ci,
  `success` tinyint(1) NOT NULL,
  `failure_reason` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  `created_by_user_id` int DEFAULT NULL,
  `updated_by_user_id` int DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted_by_user_id` int DEFAULT NULL,
  `version` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_login_attempts_ip_address` (`ip_address`),
  KEY `ix_login_attempts_user_id` (`user_id`),
  KEY `ix_login_attempts_username_attempted` (`username_attempted`),
  CONSTRAINT `fk_login_attempts_user_id_users` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=32 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO `login_attempts` (user_id, username_attempted, ip_address, user_agent, success, failure_reason, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "admin", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", 1, NULL, 1, datetime.datetime(2026, 11, 16, 6, 42, 48), datetime.datetime(2026, 11, 16, 6, 42, 48), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `login_attempts` (user_id, username_attempted, ip_address, user_agent, success, failure_reason, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "admin", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", 0, "invalid_password", 2, datetime.datetime(2026, 11, 16, 8, 6, 31), datetime.datetime(2026, 11, 16, 8, 6, 31), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `login_attempts` (user_id, username_attempted, ip_address, user_agent, success, failure_reason, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "admin", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", 0, "invalid_password", 3, datetime.datetime(2026, 11, 16, 8, 6, 42), datetime.datetime(2026, 11, 16, 8, 6, 42), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `login_attempts` (user_id, username_attempted, ip_address, user_agent, success, failure_reason, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "admin", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", 0, "invalid_password", 4, datetime.datetime(2026, 11, 16, 8, 6, 51), datetime.datetime(2026, 11, 16, 8, 6, 51), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `login_attempts` (user_id, username_attempted, ip_address, user_agent, success, failure_reason, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "admin", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", 0, "invalid_password", 5, datetime.datetime(2026, 11, 16, 8, 9, 50), datetime.datetime(2026, 11, 16, 8, 9, 50), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `login_attempts` (user_id, username_attempted, ip_address, user_agent, success, failure_reason, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "admin", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", 0, "account_locked", 6, datetime.datetime(2026, 11, 16, 8, 11, 23), datetime.datetime(2026, 11, 16, 8, 11, 23), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `login_attempts` (user_id, username_attempted, ip_address, user_agent, success, failure_reason, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "admin", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", 0, "account_locked", 7, datetime.datetime(2026, 11, 16, 8, 12, 5), datetime.datetime(2026, 11, 16, 8, 12, 5), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `login_attempts` (user_id, username_attempted, ip_address, user_agent, success, failure_reason, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "admin", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", 1, NULL, 8, datetime.datetime(2026, 11, 16, 8, 12, 27), datetime.datetime(2026, 11, 16, 8, 12, 27), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `login_attempts` (user_id, username_attempted, ip_address, user_agent, success, failure_reason, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (NULL, "agent", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", 0, "user_not_found", 9, datetime.datetime(2026, 11, 16, 8, 41, 33), datetime.datetime(2026, 11, 16, 8, 41, 33), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `login_attempts` (user_id, username_attempted, ip_address, user_agent, success, failure_reason, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (3, "support", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", 1, NULL, 10, datetime.datetime(2026, 11, 16, 8, 41, 52), datetime.datetime(2026, 11, 16, 8, 41, 52), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `login_attempts` (user_id, username_attempted, ip_address, user_agent, success, failure_reason, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (6, "demo_support", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", 0, "invalid_password", 11, datetime.datetime(2026, 11, 16, 8, 43, 33), datetime.datetime(2026, 11, 16, 8, 43, 33), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `login_attempts` (user_id, username_attempted, ip_address, user_agent, success, failure_reason, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (6, "demo_support", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", 1, NULL, 12, datetime.datetime(2026, 11, 16, 8, 43, 45), datetime.datetime(2026, 11, 16, 8, 43, 45), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `login_attempts` (user_id, username_attempted, ip_address, user_agent, success, failure_reason, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "admin", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", 0, "invalid_password", 13, datetime.datetime(2026, 11, 19, 7, 28, 3), datetime.datetime(2026, 11, 19, 7, 28, 3), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `login_attempts` (user_id, username_attempted, ip_address, user_agent, success, failure_reason, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "admin", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", 0, "invalid_password", 14, datetime.datetime(2026, 11, 19, 7, 28, 10), datetime.datetime(2026, 11, 19, 7, 28, 10), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `login_attempts` (user_id, username_attempted, ip_address, user_agent, success, failure_reason, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "admin", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", 1, NULL, 15, datetime.datetime(2026, 11, 19, 7, 28, 22), datetime.datetime(2026, 11, 19, 7, 28, 22), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `login_attempts` (user_id, username_attempted, ip_address, user_agent, success, failure_reason, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (2, "helpdesk", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", 1, NULL, 16, datetime.datetime(2026, 11, 19, 7, 46, 25), datetime.datetime(2026, 11, 19, 7, 46, 25), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `login_attempts` (user_id, username_attempted, ip_address, user_agent, success, failure_reason, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (3, "support", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", 1, NULL, 17, datetime.datetime(2026, 11, 19, 7, 46, 57), datetime.datetime(2026, 11, 19, 7, 46, 57), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `login_attempts` (user_id, username_attempted, ip_address, user_agent, success, failure_reason, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (4, "user", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", 1, NULL, 18, datetime.datetime(2026, 11, 19, 7, 47, 16), datetime.datetime(2026, 11, 19, 7, 47, 16), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `login_attempts` (user_id, username_attempted, ip_address, user_agent, success, failure_reason, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "admin", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", 1, NULL, 19, datetime.datetime(2026, 11, 19, 7, 47, 41), datetime.datetime(2026, 11, 19, 7, 47, 41), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `login_attempts` (user_id, username_attempted, ip_address, user_agent, success, failure_reason, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (4, "user", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", 1, NULL, 20, datetime.datetime(2026, 11, 19, 7, 48, 45), datetime.datetime(2026, 11, 19, 7, 48, 45), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `login_attempts` (user_id, username_attempted, ip_address, user_agent, success, failure_reason, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (4, "user", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", 1, NULL, 21, datetime.datetime(2026, 11, 19, 7, 51, 8), datetime.datetime(2026, 11, 19, 7, 51, 8), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `login_attempts` (user_id, username_attempted, ip_address, user_agent, success, failure_reason, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (4, "user", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", 0, "invalid_password", 22, datetime.datetime(2026, 11, 19, 7, 51, 16), datetime.datetime(2026, 11, 19, 7, 51, 16), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `login_attempts` (user_id, username_attempted, ip_address, user_agent, success, failure_reason, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (3, "support", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", 1, NULL, 23, datetime.datetime(2026, 11, 19, 7, 51, 57), datetime.datetime(2026, 11, 19, 7, 51, 57), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `login_attempts` (user_id, username_attempted, ip_address, user_agent, success, failure_reason, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (3, "support", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", 1, NULL, 24, datetime.datetime(2026, 11, 19, 7, 52, 9), datetime.datetime(2026, 11, 19, 7, 52, 9), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `login_attempts` (user_id, username_attempted, ip_address, user_agent, success, failure_reason, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (4, "user", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", 1, NULL, 25, datetime.datetime(2026, 11, 19, 7, 53, 29), datetime.datetime(2026, 11, 19, 7, 53, 29), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `login_attempts` (user_id, username_attempted, ip_address, user_agent, success, failure_reason, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "admin", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", 1, NULL, 26, datetime.datetime(2026, 11, 19, 9, 9, 29), datetime.datetime(2026, 11, 19, 9, 9, 29), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `login_attempts` (user_id, username_attempted, ip_address, user_agent, success, failure_reason, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "admin", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", 1, NULL, 27, datetime.datetime(2026, 11, 19, 13, 58, 17), datetime.datetime(2026, 11, 19, 13, 58, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `login_attempts` (user_id, username_attempted, ip_address, user_agent, success, failure_reason, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "admin", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", 1, NULL, 28, datetime.datetime(2026, 11, 19, 14, 20, 17), datetime.datetime(2026, 11, 19, 14, 20, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `login_attempts` (user_id, username_attempted, ip_address, user_agent, success, failure_reason, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "admin", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Qoder/0.5.5 Chrome/150.0.7871.250 Electron/43.8.4 Safari/537.36", 0, "invalid_password", 29, datetime.datetime(2026, 11, 19, 14, 48, 10), datetime.datetime(2026, 11, 19, 14, 48, 10), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `login_attempts` (user_id, username_attempted, ip_address, user_agent, success, failure_reason, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "admin", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Qoder/0.5.5 Chrome/150.0.7871.250 Electron/43.8.4 Safari/537.36", 1, NULL, 30, datetime.datetime(2026, 11, 19, 14, 59, 44), datetime.datetime(2026, 11, 19, 14, 59, 44), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `login_attempts` (user_id, username_attempted, ip_address, user_agent, success, failure_reason, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (1, "admin", "127.0.0.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36", 1, NULL, 31, datetime.datetime(2026, 11, 19, 15, 3, 47), datetime.datetime(2026, 11, 19, 15, 3, 47), NULL, NULL, 1, NULL, NULL, 1);
-- Table: notifications
-- Row count: 3
CREATE TABLE `notifications` (
  `user_id` int NOT NULL,
  `complaint_id` int DEFAULT NULL,
  `title` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `message` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `notification_type` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_read` tinyint(1) NOT NULL,
  `read_at` datetime DEFAULT NULL,
  `related_entity_type` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `related_entity_id` int DEFAULT NULL,
  `action_url` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `action_label` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `priority` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  `created_by_user_id` int DEFAULT NULL,
  `updated_by_user_id` int DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted_by_user_id` int DEFAULT NULL,
  `version` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_notifications_complaint_id` (`complaint_id`),
  KEY `ix_notifications_notification_type` (`notification_type`),
  KEY `ix_notifications_user_id` (`user_id`),
  CONSTRAINT `fk_notifications_complaint_id_complaints` FOREIGN KEY (`complaint_id`) REFERENCES `complaints` (`id`),
  CONSTRAINT `fk_notifications_user_id_users` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=82 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO `notifications` (user_id, complaint_id, title, message, notification_type, is_read, read_at, related_entity_type, related_entity_id, action_url, action_label, priority, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (3, 7, "New Complaint Assigned", "You have been assigned to complaint ITC-2026-000001: test", "assignment", 0, NULL, NULL, NULL, "/complaints/7", "View Complaint", "high", 1, datetime.datetime(2026, 11, 16, 8, 41, 15), datetime.datetime(2026, 11, 16, 8, 41, 15), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `notifications` (user_id, complaint_id, title, message, notification_type, is_read, read_at, related_entity_type, related_entity_id, action_url, action_label, priority, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (6, 8, "New Complaint Assigned", "You have been assigned to complaint ITC-2026-000002: test2", "assignment", 0, NULL, NULL, NULL, "/complaints/8", "View Complaint", "high", 2, datetime.datetime(2026, 11, 16, 8, 42, 32), datetime.datetime(2026, 11, 16, 8, 42, 32), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `notifications` (user_id, complaint_id, title, message, notification_type, is_read, read_at, related_entity_type, related_entity_id, action_url, action_label, priority, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (3, 9, "New Complaint Assigned", "You have been assigned to complaint ITC-2026-000003: user test", "assignment", 0, NULL, NULL, NULL, "/complaints/9", "View Complaint", "high", 27, datetime.datetime(2026, 11, 19, 7, 49, 47), datetime.datetime(2026, 11, 19, 7, 49, 47), NULL, NULL, 1, NULL, NULL, 1);
-- Table: permissions
-- Row count: 36
CREATE TABLE `permissions` (
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `display_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `module` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `action` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  `created_by_user_id` int DEFAULT NULL,
  `updated_by_user_id` int DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted_by_user_id` int DEFAULT NULL,
  `version` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_permissions_name` (`name`),
  KEY `ix_permissions_module` (`module`)
) ENGINE=InnoDB AUTO_INCREMENT=37 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO `permissions` (name, display_name, description, module, action, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("dashboard.view", "View Dashboard", NULL, "dashboard", "view", 1, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `permissions` (name, display_name, description, module, action, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("complaints.create", "Create Complaint", NULL, "complaints", "create", 2, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `permissions` (name, display_name, description, module, action, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("complaints.view_all", "View All Complaints", NULL, "complaints", "view_all", 3, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `permissions` (name, display_name, description, module, action, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("complaints.view_confidential", "View Confidential Complaints", NULL, "complaints", "view_confidential", 4, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `permissions` (name, display_name, description, module, action, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("complaints.view_my", "View My Complaints", NULL, "complaints", "view_my", 5, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `permissions` (name, display_name, description, module, action, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("complaints.edit", "Edit Complaint", NULL, "complaints", "edit", 6, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `permissions` (name, display_name, description, module, action, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("complaints.assign", "Assign Complaint", NULL, "complaints", "assign", 7, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `permissions` (name, display_name, description, module, action, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("complaints.transfer", "Transfer Complaint", NULL, "complaints", "transfer", 8, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `permissions` (name, display_name, description, module, action, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("complaints.change_status_own", "Change Status of Own Complaints", NULL, "complaints", "change_status_own", 9, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `permissions` (name, display_name, description, module, action, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("complaints.change_status_all", "Change Status of Any Complaint", NULL, "complaints", "change_status_all", 10, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `permissions` (name, display_name, description, module, action, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("complaints.status_unlock", "Access Restricted Statuses", NULL, "complaints", "status_unlock", 11, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `permissions` (name, display_name, description, module, action, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("complaints.delete", "Delete Complaints", NULL, "complaints", "delete", 12, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `permissions` (name, display_name, description, module, action, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("comments.add_internal", "Add Internal Comment", NULL, "comments", "add_internal", 13, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `permissions` (name, display_name, description, module, action, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("comments.add_reporter_visible", "Add Reporter Comment", NULL, "comments", "add_reporter_visible", 14, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `permissions` (name, display_name, description, module, action, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("comments.view_internal", "View Internal Comments", NULL, "comments", "view_internal", 15, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `permissions` (name, display_name, description, module, action, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("attachments.upload", "Upload Attachments", NULL, "attachments", "upload", 16, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `permissions` (name, display_name, description, module, action, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("attachments.download_all", "Download All Attachments", NULL, "attachments", "download_all", 17, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `permissions` (name, display_name, description, module, action, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("attachments.delete", "Delete Any Attachment", NULL, "attachments", "delete", 18, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `permissions` (name, display_name, description, module, action, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("attachments.delete_own", "Delete Own Attachment", NULL, "attachments", "delete_own", 19, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `permissions` (name, display_name, description, module, action, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("reports.view", "View Reports", NULL, "reports", "view", 20, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `permissions` (name, display_name, description, module, action, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("reports.export", "Export Reports", NULL, "reports", "export", 21, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `permissions` (name, display_name, description, module, action, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("users.view", "View Users", NULL, "users", "view", 22, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `permissions` (name, display_name, description, module, action, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("users.edit", "Edit Users", NULL, "users", "edit", 23, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `permissions` (name, display_name, description, module, action, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("users.manage", "Manage Users", NULL, "users", "manage", 24, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `permissions` (name, display_name, description, module, action, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("roles.manage", "Manage Roles", NULL, "roles", "manage", 25, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `permissions` (name, display_name, description, module, action, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("permissions.manage", "Manage Permissions", NULL, "permissions", "manage", 26, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `permissions` (name, display_name, description, module, action, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("config.manage", "Manage Configuration", NULL, "config", "manage", 27, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `permissions` (name, display_name, description, module, action, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("settings.manage", "Manage System Settings", NULL, "settings", "manage", 28, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `permissions` (name, display_name, description, module, action, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("departments.manage", "Manage Departments", NULL, "departments", "manage", 29, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `permissions` (name, display_name, description, module, action, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("categories.manage", "Manage Categories", NULL, "categories", "manage", 30, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `permissions` (name, display_name, description, module, action, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("priorities.manage", "Manage Priorities", NULL, "priorities", "manage", 31, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `permissions` (name, display_name, description, module, action, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("statuses.manage", "Manage Statuses", NULL, "statuses", "manage", 32, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `permissions` (name, display_name, description, module, action, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("sla.manage", "Manage SLA Policies", NULL, "sla", "manage", 33, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `permissions` (name, display_name, description, module, action, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("software.manage", "Manage Software Catalog", NULL, "software", "manage", 34, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `permissions` (name, display_name, description, module, action, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("audit.view", "View Audit Logs", NULL, "audit", "view", 35, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `permissions` (name, display_name, description, module, action, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("notifications.view", "View Notifications", NULL, "notifications", "view", 36, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, 1, NULL, NULL, 1);
-- Table: priorities
-- Row count: 4
CREATE TABLE `priorities` (
  `name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `level` int NOT NULL,
  `color` varchar(7) COLLATE utf8mb4_unicode_ci NOT NULL,
  `icon` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `sort_order` int NOT NULL,
  `sla_response_hours` float DEFAULT NULL,
  `sla_resolution_hours` float DEFAULT NULL,
  `escalation_hours` float DEFAULT NULL,
  `notify_assigned` tinyint(1) NOT NULL,
  `notify_on_breach` tinyint(1) NOT NULL,
  `default_sla_policy_id` int DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  `created_by_user_id` int DEFAULT NULL,
  `updated_by_user_id` int DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted_by_user_id` int DEFAULT NULL,
  `version` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_priorities_code` (`code`),
  UNIQUE KEY `ix_priorities_name` (`name`),
  KEY `ix_priorities_level` (`level`),
  KEY `fk_priorities_default_sla` (`default_sla_policy_id`),
  CONSTRAINT `fk_priorities_default_sla` FOREIGN KEY (`default_sla_policy_id`) REFERENCES `sla_policies` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO `priorities` (name, code, description, level, color, icon, is_active, sort_order, sla_response_hours, sla_resolution_hours, escalation_hours, notify_assigned, notify_on_breach, default_sla_policy_id, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id, version) VALUES ("Critical", "CRITICAL", "Patient safety or full outage", 1, "#EF4444", "alert-octagon", 1, 1, NULL, NULL, NULL, 0, 0, 1, 1, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 59), NULL, NULL, NULL, NULL, 1);
INSERT INTO `priorities` (name, code, description, level, color, icon, is_active, sort_order, sla_response_hours, sla_resolution_hours, escalation_hours, notify_assigned, notify_on_breach, default_sla_policy_id, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id, version) VALUES ("High", "HIGH", "Major disruption to clinical work", 2, "#F97316", "alert-triangle", 1, 2, NULL, NULL, NULL, 0, 0, 2, 2, datetime.datetime(2026, 11, 16, 6, 40, 18), datetime.datetime(2026, 11, 16, 6, 59), NULL, NULL, NULL, NULL, 1);
INSERT INTO `priorities` (name, code, description, level, color, icon, is_active, sort_order, sla_response_hours, sla_resolution_hours, escalation_hours, notify_assigned, notify_on_breach, default_sla_policy_id, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id, version) VALUES ("Medium", "MEDIUM", "Limited impact with a workaround", 3, "#3B82F6", "alert-circle", 1, 3, NULL, NULL, NULL, 0, 0, 3, 3, datetime.datetime(2026, 11, 16, 6, 40, 18), datetime.datetime(2026, 11, 16, 6, 59), NULL, NULL, NULL, NULL, 1);
INSERT INTO `priorities` (name, code, description, level, color, icon, is_active, sort_order, sla_response_hours, sla_resolution_hours, escalation_hours, notify_assigned, notify_on_breach, default_sla_policy_id, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id, version) VALUES ("Low", "LOW", "Minor or cosmetic issue", 4, "#6B7280", "info", 1, 4, NULL, NULL, NULL, 0, 0, 4, 4, datetime.datetime(2026, 11, 16, 6, 40, 18), datetime.datetime(2026, 11, 16, 6, 59), NULL, NULL, NULL, NULL, 1);
-- Table: role_permissions
-- Row count: 74
CREATE TABLE `role_permissions` (
  `role_id` int NOT NULL,
  `permission_id` int NOT NULL,
  `assigned_at` datetime NOT NULL,
  `assigned_by_user_id` int DEFAULT NULL,
  PRIMARY KEY (`role_id`,`permission_id`),
  KEY `fk_role_permissions_assigned_by_user_id_users` (`assigned_by_user_id`),
  KEY `fk_role_permissions_permission_id_permissions` (`permission_id`),
  CONSTRAINT `fk_role_permissions_assigned_by_user_id_users` FOREIGN KEY (`assigned_by_user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_role_permissions_permission_id_permissions` FOREIGN KEY (`permission_id`) REFERENCES `permissions` (`id`),
  CONSTRAINT `fk_role_permissions_role_id_roles` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (1, 1, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (1, 2, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (1, 3, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (1, 4, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (1, 5, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (1, 6, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (1, 7, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (1, 8, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (1, 9, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (1, 10, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (1, 11, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (1, 12, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (1, 13, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (1, 14, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (1, 15, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (1, 16, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (1, 17, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (1, 18, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (1, 19, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (1, 20, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (1, 21, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (1, 22, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (1, 23, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (1, 24, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (1, 25, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (1, 26, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (1, 27, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (1, 28, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (1, 29, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (1, 30, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (1, 31, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (1, 32, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (1, 33, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (1, 34, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (1, 35, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (1, 36, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (2, 1, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (2, 2, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (2, 3, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (2, 5, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (2, 6, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (2, 7, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (2, 8, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (2, 9, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (2, 10, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (2, 11, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (2, 13, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (2, 14, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (2, 15, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (2, 16, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (2, 17, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (2, 18, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (2, 20, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (2, 21, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (2, 22, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (3, 1, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (3, 2, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (3, 5, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (3, 6, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (3, 8, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (3, 9, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (3, 13, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (3, 14, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (3, 15, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (3, 16, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (3, 17, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (3, 20, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (3, 21, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (3, 36, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (4, 1, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (4, 2, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (4, 14, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (4, 16, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
INSERT INTO `role_permissions` (role_id, permission_id, assigned_at, assigned_by_user_id) VALUES (4, 19, datetime.datetime(2026, 11, 16, 6, 40, 17), NULL);
-- Table: roles
-- Row count: 4
CREATE TABLE `roles` (
  `name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `display_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `is_system` tinyint(1) NOT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  `created_by_user_id` int DEFAULT NULL,
  `updated_by_user_id` int DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted_by_user_id` int DEFAULT NULL,
  `version` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_roles_name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO `roles` (name, display_name, description, is_system, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("admin", "Administrator", "Development demo role: Administrator", 1, 1, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 18), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `roles` (name, display_name, description, is_system, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("helpdesk_agent", "Helpdesk Agent", "Development demo role: Helpdesk Agent", 1, 2, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 59), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `roles` (name, display_name, description, is_system, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("support_agent", "Support Agent", "Development demo role: Support Agent", 1, 3, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 59, 1), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `roles` (name, display_name, description, is_system, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES ("user", "End User", "Development demo role: End User", 1, 4, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 59, 1), NULL, NULL, 1, NULL, NULL, 1);
-- Table: sla_history
-- Row count: 3
CREATE TABLE `sla_history` (
  `complaint_id` int NOT NULL,
  `sla_policy_id` int DEFAULT NULL,
  `response_deadline` datetime DEFAULT NULL,
  `resolution_deadline` datetime DEFAULT NULL,
  `calculation_method` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `business_hours_used` tinyint(1) NOT NULL,
  `working_schedule_id` int DEFAULT NULL,
  `is_paused` tinyint(1) NOT NULL,
  `paused_at` datetime DEFAULT NULL,
  `paused_by_status_id` int DEFAULT NULL,
  `pause_reason` text COLLATE utf8mb4_unicode_ci,
  `resumed_at` datetime DEFAULT NULL,
  `resume_reason` text COLLATE utf8mb4_unicode_ci,
  `total_paused_minutes` int NOT NULL,
  `response_breached` tinyint(1) NOT NULL,
  `resolution_breached` tinyint(1) NOT NULL,
  `response_breached_at` datetime DEFAULT NULL,
  `resolution_breached_at` datetime DEFAULT NULL,
  `calculated_at` datetime NOT NULL,
  `calculated_by_user_id` int DEFAULT NULL,
  `notes` text COLLATE utf8mb4_unicode_ci,
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  `created_by_user_id` int DEFAULT NULL,
  `updated_by_user_id` int DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted_by_user_id` int DEFAULT NULL,
  `version` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_sla_history_complaint_id` (`complaint_id`),
  KEY `ix_sla_history_resolution_deadline` (`resolution_deadline`),
  KEY `ix_sla_history_response_deadline` (`response_deadline`),
  KEY `fk_sla_history_calculated_by_user_id_users` (`calculated_by_user_id`),
  KEY `fk_sla_history_paused_by_status_id_statuses` (`paused_by_status_id`),
  KEY `fk_sla_history_sla_policy_id_sla_policies` (`sla_policy_id`),
  KEY `fk_sla_history_working_schedule_id_working_schedules` (`working_schedule_id`),
  CONSTRAINT `fk_sla_history_calculated_by_user_id_users` FOREIGN KEY (`calculated_by_user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_sla_history_complaint_id_complaints` FOREIGN KEY (`complaint_id`) REFERENCES `complaints` (`id`),
  CONSTRAINT `fk_sla_history_paused_by_status_id_statuses` FOREIGN KEY (`paused_by_status_id`) REFERENCES `statuses` (`id`),
  CONSTRAINT `fk_sla_history_sla_policy_id_sla_policies` FOREIGN KEY (`sla_policy_id`) REFERENCES `sla_policies` (`id`),
  CONSTRAINT `fk_sla_history_working_schedule_id_working_schedules` FOREIGN KEY (`working_schedule_id`) REFERENCES `working_schedules` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO `sla_history` (complaint_id, sla_policy_id, response_deadline, resolution_deadline, calculation_method, business_hours_used, working_schedule_id, is_paused, paused_at, paused_by_status_id, pause_reason, resumed_at, resume_reason, total_paused_minutes, response_breached, resolution_breached, response_breached_at, resolution_breached_at, calculated_at, calculated_by_user_id, notes, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (7, 1, datetime.datetime(2026, 11, 16, 10, 0), datetime.datetime(2026, 11, 16, 13, 0), "business_hours", 1, 1, 0, NULL, NULL, NULL, NULL, NULL, 0, 0, 0, NULL, NULL, datetime.datetime(2026, 11, 16, 8, 41, 15), 1, "Initial SLA calculation using policy: Critical Priority SLA", 1, datetime.datetime(2026, 11, 16, 8, 41, 15), datetime.datetime(2026, 11, 16, 8, 41, 15), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `sla_history` (complaint_id, sla_policy_id, response_deadline, resolution_deadline, calculation_method, business_hours_used, working_schedule_id, is_paused, paused_at, paused_by_status_id, pause_reason, resumed_at, resume_reason, total_paused_minutes, response_breached, resolution_breached, response_breached_at, resolution_breached_at, calculated_at, calculated_by_user_id, notes, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (8, 1, datetime.datetime(2026, 11, 16, 10, 0), datetime.datetime(2026, 11, 16, 13, 0), "business_hours", 1, 1, 0, NULL, NULL, NULL, NULL, NULL, 0, 0, 0, NULL, NULL, datetime.datetime(2026, 11, 16, 8, 42, 32), 1, "Initial SLA calculation using policy: Critical Priority SLA", 2, datetime.datetime(2026, 11, 16, 8, 42, 32), datetime.datetime(2026, 11, 16, 8, 42, 32), NULL, NULL, 1, NULL, NULL, 1);
INSERT INTO `sla_history` (complaint_id, sla_policy_id, response_deadline, resolution_deadline, calculation_method, business_hours_used, working_schedule_id, is_paused, paused_at, paused_by_status_id, pause_reason, resumed_at, resume_reason, total_paused_minutes, response_breached, resolution_breached, response_breached_at, resolution_breached_at, calculated_at, calculated_by_user_id, notes, id, created_at, updated_at, created_by_user_id, updated_by_user_id, is_active, deleted_at, deleted_by_user_id, version) VALUES (9, 1, datetime.datetime(2026, 11, 19, 10, 0), datetime.datetime(2026, 11, 19, 13, 0), "business_hours", 1, 1, 0, NULL, NULL, NULL, NULL, NULL, 0, 0, 0, NULL, NULL, datetime.datetime(2026, 11, 19, 7, 49, 47), 4, "Initial SLA calculation using policy: Critical Priority SLA", 3, datetime.datetime(2026, 11, 19, 7, 49, 47), datetime.datetime(2026, 11, 19, 7, 49, 47), NULL, NULL, 1, NULL, NULL, 1);
-- Table: sla_policies
-- Row count: 4
CREATE TABLE `sla_policies` (
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `department_id` int DEFAULT NULL,
  `priority_id` int DEFAULT NULL,
  `category_id` int DEFAULT NULL,
  `response_target_minutes` int NOT NULL,
  `resolution_target_minutes` int NOT NULL,
  `use_business_hours` tinyint(1) NOT NULL,
  `working_schedule_id` int DEFAULT NULL,
  `escalation_enabled` tinyint(1) NOT NULL,
  `escalation_levels` json DEFAULT NULL,
  `pause_on_pending_info` tinyint(1) NOT NULL,
  `pause_on_hold` tinyint(1) NOT NULL,
  `pause_on_reassignment` tinyint(1) NOT NULL,
  `pause_on_reopen` tinyint(1) NOT NULL,
  `pause_on_status_ids` json DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `is_default` tinyint(1) NOT NULL,
  `sort_order` int NOT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  `created_by_user_id` int DEFAULT NULL,
  `updated_by_user_id` int DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted_by_user_id` int DEFAULT NULL,
  `version` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_sla_policies_name` (`name`),
  KEY `fk_sla_policies_category` (`category_id`),
  KEY `fk_sla_policies_department_id_departments` (`department_id`),
  KEY `fk_sla_policies_priority` (`priority_id`),
  KEY `fk_sla_policies_working_schedule_id_working_schedules` (`working_schedule_id`),
  CONSTRAINT `fk_sla_policies_category` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`),
  CONSTRAINT `fk_sla_policies_department_id_departments` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`),
  CONSTRAINT `fk_sla_policies_priority` FOREIGN KEY (`priority_id`) REFERENCES `priorities` (`id`),
  CONSTRAINT `fk_sla_policies_working_schedule_id_working_schedules` FOREIGN KEY (`working_schedule_id`) REFERENCES `working_schedules` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO `sla_policies` (name, description, department_id, priority_id, category_id, response_target_minutes, resolution_target_minutes, use_business_hours, working_schedule_id, escalation_enabled, escalation_levels, pause_on_pending_info, pause_on_hold, pause_on_reassignment, pause_on_reopen, pause_on_status_ids, is_active, is_default, sort_order, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id, version) VALUES ("Critical Priority SLA", "Development SLA for Critical", NULL, 1, NULL, 60, 240, 1, 1, 1, NULL, 1, 1, 0, 1, NULL, 1, 0, 1, 1, datetime.datetime(2026, 11, 16, 6, 40, 18), datetime.datetime(2026, 11, 16, 6, 40, 18), NULL, NULL, NULL, NULL, 1);
INSERT INTO `sla_policies` (name, description, department_id, priority_id, category_id, response_target_minutes, resolution_target_minutes, use_business_hours, working_schedule_id, escalation_enabled, escalation_levels, pause_on_pending_info, pause_on_hold, pause_on_reassignment, pause_on_reopen, pause_on_status_ids, is_active, is_default, sort_order, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id, version) VALUES ("High Priority SLA", "Development SLA for High", NULL, 2, NULL, 240, 1440, 1, 1, 1, NULL, 1, 1, 0, 1, NULL, 1, 0, 2, 2, datetime.datetime(2026, 11, 16, 6, 40, 18), datetime.datetime(2026, 11, 16, 6, 40, 18), NULL, NULL, NULL, NULL, 1);
INSERT INTO `sla_policies` (name, description, department_id, priority_id, category_id, response_target_minutes, resolution_target_minutes, use_business_hours, working_schedule_id, escalation_enabled, escalation_levels, pause_on_pending_info, pause_on_hold, pause_on_reassignment, pause_on_reopen, pause_on_status_ids, is_active, is_default, sort_order, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id, version) VALUES ("Medium Priority SLA", "Development SLA for Medium", NULL, 3, NULL, 480, 2880, 1, 1, 0, NULL, 1, 1, 0, 1, NULL, 1, 1, 3, 3, datetime.datetime(2026, 11, 16, 6, 40, 18), datetime.datetime(2026, 11, 16, 6, 40, 18), NULL, NULL, NULL, NULL, 1);
INSERT INTO `sla_policies` (name, description, department_id, priority_id, category_id, response_target_minutes, resolution_target_minutes, use_business_hours, working_schedule_id, escalation_enabled, escalation_levels, pause_on_pending_info, pause_on_hold, pause_on_reassignment, pause_on_reopen, pause_on_status_ids, is_active, is_default, sort_order, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id, version) VALUES ("Low Priority SLA", "Development SLA for Low", NULL, 4, NULL, 1440, 5760, 1, 1, 0, NULL, 1, 1, 0, 1, NULL, 1, 0, 4, 4, datetime.datetime(2026, 11, 16, 6, 40, 18), datetime.datetime(2026, 11, 16, 6, 40, 18), NULL, NULL, NULL, NULL, 1);
-- Table: software_catalog
-- Row count: 8
CREATE TABLE `software_catalog` (
  `name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `code` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `version` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `vendor` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `vendor_contact` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `vendor_support_url` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `license_type` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `license_expiry` date DEFAULT NULL,
  `department_id` int DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `sort_order` int NOT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  `created_by_user_id` int DEFAULT NULL,
  `updated_by_user_id` int DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted_by_user_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_software_catalog_code` (`code`),
  UNIQUE KEY `ix_software_catalog_name` (`name`),
  KEY `fk_software_catalog_department_id_departments` (`department_id`),
  CONSTRAINT `fk_software_catalog_department_id_departments` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO `software_catalog` (name, code, description, version, vendor, vendor_contact, vendor_support_url, license_type, license_expiry, department_id, is_active, sort_order, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id) VALUES ("Hospital Information System", "HIS", "Core hospital information system", NULL, "Vendor A", NULL, NULL, NULL, NULL, 3, 1, 0, 1, datetime.datetime(2026, 11, 16, 6, 40, 18), datetime.datetime(2026, 11, 16, 6, 40, 18), NULL, NULL, NULL, NULL);
INSERT INTO `software_catalog` (name, code, description, version, vendor, vendor_contact, vendor_support_url, license_type, license_expiry, department_id, is_active, sort_order, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id) VALUES ("Laboratory Information System", "LIS", "Lab order and result management", NULL, "Vendor B", NULL, NULL, NULL, NULL, 3, 1, 0, 2, datetime.datetime(2026, 11, 16, 6, 40, 18), datetime.datetime(2026, 11, 16, 6, 40, 18), NULL, NULL, NULL, NULL);
INSERT INTO `software_catalog` (name, code, description, version, vendor, vendor_contact, vendor_support_url, license_type, license_expiry, department_id, is_active, sort_order, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id) VALUES ("PACS", "PACS", "Medical imaging archive", NULL, "Vendor C", NULL, NULL, NULL, NULL, 3, 1, 0, 3, datetime.datetime(2026, 11, 16, 6, 40, 18), datetime.datetime(2026, 11, 16, 6, 40, 18), NULL, NULL, NULL, NULL);
INSERT INTO `software_catalog` (name, code, description, version, vendor, vendor_contact, vendor_support_url, license_type, license_expiry, department_id, is_active, sort_order, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id) VALUES ("Radiology Information System", "RIS", "Radiology workflow", NULL, "Vendor C", NULL, NULL, NULL, NULL, 3, 1, 0, 4, datetime.datetime(2026, 11, 16, 6, 40, 18), datetime.datetime(2026, 11, 16, 6, 40, 18), NULL, NULL, NULL, NULL);
INSERT INTO `software_catalog` (name, code, description, version, vendor, vendor_contact, vendor_support_url, license_type, license_expiry, department_id, is_active, sort_order, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id) VALUES ("Pharmacy System", "PHARM", "Pharmacy dispensing and stock", NULL, "Vendor D", NULL, NULL, NULL, NULL, 3, 1, 0, 5, datetime.datetime(2026, 11, 16, 6, 40, 18), datetime.datetime(2026, 11, 16, 6, 40, 18), NULL, NULL, NULL, NULL);
INSERT INTO `software_catalog` (name, code, description, version, vendor, vendor_contact, vendor_support_url, license_type, license_expiry, department_id, is_active, sort_order, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id) VALUES ("Billing & ERP", "ERP", "Finance and billing suite", NULL, "Vendor E", NULL, NULL, NULL, NULL, 3, 1, 0, 6, datetime.datetime(2026, 11, 16, 6, 40, 18), datetime.datetime(2026, 11, 16, 6, 40, 18), NULL, NULL, NULL, NULL);
INSERT INTO `software_catalog` (name, code, description, version, vendor, vendor_contact, vendor_support_url, license_type, license_expiry, department_id, is_active, sort_order, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id) VALUES ("Email", "EMAIL", "Corporate email service", NULL, "Vendor F", NULL, NULL, NULL, NULL, 3, 1, 0, 7, datetime.datetime(2026, 11, 16, 6, 40, 18), datetime.datetime(2026, 11, 16, 6, 40, 18), NULL, NULL, NULL, NULL);
INSERT INTO `software_catalog` (name, code, description, version, vendor, vendor_contact, vendor_support_url, license_type, license_expiry, department_id, is_active, sort_order, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id) VALUES ("Network Services", "NETWORK-SVC", "Network infrastructure", NULL, "Internal IT", NULL, NULL, NULL, NULL, 3, 1, 0, 8, datetime.datetime(2026, 11, 16, 6, 59), datetime.datetime(2026, 11, 16, 6, 59), NULL, NULL, NULL, NULL);
-- Table: statuses
-- Row count: 9
CREATE TABLE `statuses` (
  `name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `category` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_initial` tinyint(1) NOT NULL,
  `is_terminal` tinyint(1) NOT NULL,
  `requires_reason` tinyint(1) NOT NULL,
  `requires_resolution` tinyint(1) NOT NULL,
  `color` varchar(7) COLLATE utf8mb4_unicode_ci NOT NULL,
  `icon` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `sort_order` int NOT NULL,
  `allowed_transitions` json DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  `created_by_user_id` int DEFAULT NULL,
  `updated_by_user_id` int DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted_by_user_id` int DEFAULT NULL,
  `version` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_statuses_code` (`code`),
  UNIQUE KEY `ix_statuses_name` (`name`),
  KEY `ix_statuses_category` (`category`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO `statuses` (name, code, description, category, is_initial, is_terminal, requires_reason, requires_resolution, color, icon, is_active, sort_order, allowed_transitions, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id, version) VALUES ("New", "new", NULL, "open", 1, 0, 0, 0, "#3B82F6", "inbox", 1, 1, NULL, 1, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, NULL, NULL, 1);
INSERT INTO `statuses` (name, code, description, category, is_initial, is_terminal, requires_reason, requires_resolution, color, icon, is_active, sort_order, allowed_transitions, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id, version) VALUES ("Assigned", "assigned", NULL, "open", 0, 0, 0, 0, "#8B5CF6", "user-check", 1, 2, NULL, 2, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, NULL, NULL, 1);
INSERT INTO `statuses` (name, code, description, category, is_initial, is_terminal, requires_reason, requires_resolution, color, icon, is_active, sort_order, allowed_transitions, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id, version) VALUES ("In Progress", "in_progress", NULL, "in_progress", 0, 0, 0, 0, "#F59E0B", "loader", 1, 3, NULL, 3, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, NULL, NULL, 1);
INSERT INTO `statuses` (name, code, description, category, is_initial, is_terminal, requires_reason, requires_resolution, color, icon, is_active, sort_order, allowed_transitions, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id, version) VALUES ("Pending Info", "pending_info", NULL, "pending", 0, 0, 0, 0, "#F97316", "help-circle", 1, 4, NULL, 4, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, NULL, NULL, 1);
INSERT INTO `statuses` (name, code, description, category, is_initial, is_terminal, requires_reason, requires_resolution, color, icon, is_active, sort_order, allowed_transitions, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id, version) VALUES ("On Hold", "on_hold", NULL, "pending", 0, 0, 0, 0, "#6B7280", "pause", 1, 5, NULL, 5, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, NULL, NULL, 1);
INSERT INTO `statuses` (name, code, description, category, is_initial, is_terminal, requires_reason, requires_resolution, color, icon, is_active, sort_order, allowed_transitions, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id, version) VALUES ("Resolved", "resolved", NULL, "resolved", 0, 0, 0, 1, "#10B981", "check-circle", 1, 6, NULL, 6, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, NULL, NULL, 1);
INSERT INTO `statuses` (name, code, description, category, is_initial, is_terminal, requires_reason, requires_resolution, color, icon, is_active, sort_order, allowed_transitions, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id, version) VALUES ("Closed", "closed", NULL, "closed", 0, 1, 0, 0, "#4B5563", "lock", 1, 7, NULL, 7, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, NULL, NULL, 1);
INSERT INTO `statuses` (name, code, description, category, is_initial, is_terminal, requires_reason, requires_resolution, color, icon, is_active, sort_order, allowed_transitions, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id, version) VALUES ("Reopened", "reopened", NULL, "open", 0, 0, 1, 0, "#EF4444", "rotate-ccw", 1, 8, NULL, 8, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, NULL, NULL, 1);
INSERT INTO `statuses` (name, code, description, category, is_initial, is_terminal, requires_reason, requires_resolution, color, icon, is_active, sort_order, allowed_transitions, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id, version) VALUES ("Rejected", "rejected", NULL, "closed", 0, 1, 1, 0, "#DC2626", "x-circle", 1, 9, NULL, 9, datetime.datetime(2026, 11, 16, 6, 40, 17), datetime.datetime(2026, 11, 16, 6, 40, 17), NULL, NULL, NULL, NULL, 1);
-- Table: system_settings
-- Row count: 0
CREATE TABLE `system_settings` (
  `key` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `value` text COLLATE utf8mb4_unicode_ci,
  `value_type` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `category` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `is_public` tinyint(1) NOT NULL,
  `is_editable` tinyint(1) NOT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  `created_by_user_id` int DEFAULT NULL,
  `updated_by_user_id` int DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted_by_user_id` int DEFAULT NULL,
  `version` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_system_settings_key` (`key`),
  KEY `ix_system_settings_category` (`category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
-- Table: user_profiles
-- Row count: 0
CREATE TABLE `user_profiles` (
  `user_id` int NOT NULL,
  `title` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `hire_date` date DEFAULT NULL,
  `manager_id` int DEFAULT NULL,
  `avatar_path` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `preferences` json DEFAULT NULL,
  `email_notifications` tinyint(1) NOT NULL,
  `in_app_notifications` tinyint(1) NOT NULL,
  `notify_on_assignment` tinyint(1) NOT NULL,
  `notify_on_status_change` tinyint(1) NOT NULL,
  `notify_on_comments` tinyint(1) NOT NULL,
  `notify_on_sla_breach` tinyint(1) NOT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  `created_by_user_id` int DEFAULT NULL,
  `updated_by_user_id` int DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted_by_user_id` int DEFAULT NULL,
  `version` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `fk_user_profiles_manager_id_users` (`manager_id`),
  CONSTRAINT `fk_user_profiles_manager_id_users` FOREIGN KEY (`manager_id`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_user_profiles_user_id_users` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
-- Table: user_roles
-- Row count: 7
CREATE TABLE `user_roles` (
  `user_id` int NOT NULL,
  `role_id` int NOT NULL,
  `assigned_at` datetime NOT NULL,
  `assigned_by_user_id` int DEFAULT NULL,
  PRIMARY KEY (`user_id`,`role_id`),
  KEY `fk_user_roles_assigned_by_user_id_users` (`assigned_by_user_id`),
  KEY `fk_user_roles_role_id_roles` (`role_id`),
  CONSTRAINT `fk_user_roles_assigned_by_user_id_users` FOREIGN KEY (`assigned_by_user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_user_roles_role_id_roles` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`),
  CONSTRAINT `fk_user_roles_user_id_users` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO `user_roles` (user_id, role_id, assigned_at, assigned_by_user_id) VALUES (1, 1, datetime.datetime(2026, 11, 16, 6, 40, 18), NULL);
INSERT INTO `user_roles` (user_id, role_id, assigned_at, assigned_by_user_id) VALUES (2, 2, datetime.datetime(2026, 11, 16, 6, 40, 18), NULL);
INSERT INTO `user_roles` (user_id, role_id, assigned_at, assigned_by_user_id) VALUES (3, 3, datetime.datetime(2026, 11, 16, 6, 40, 18), NULL);
INSERT INTO `user_roles` (user_id, role_id, assigned_at, assigned_by_user_id) VALUES (4, 4, datetime.datetime(2026, 11, 16, 6, 40, 18), NULL);
INSERT INTO `user_roles` (user_id, role_id, assigned_at, assigned_by_user_id) VALUES (5, 2, datetime.datetime(2026, 11, 16, 6, 59), NULL);
INSERT INTO `user_roles` (user_id, role_id, assigned_at, assigned_by_user_id) VALUES (6, 3, datetime.datetime(2026, 11, 16, 6, 59, 1), NULL);
INSERT INTO `user_roles` (user_id, role_id, assigned_at, assigned_by_user_id) VALUES (7, 4, datetime.datetime(2026, 11, 16, 6, 59, 1), NULL);
-- Table: users
-- Row count: 7
CREATE TABLE `users` (
  `username` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `password_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `employee_number` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `first_name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `phone` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `extension` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `is_locked` tinyint(1) NOT NULL,
  `locked_at` datetime DEFAULT NULL,
  `lock_reason` text COLLATE utf8mb4_unicode_ci,
  `last_login_at` datetime DEFAULT NULL,
  `last_login_ip` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `failed_login_attempts` int NOT NULL,
  `last_failed_login_at` datetime DEFAULT NULL,
  `password_changed_at` datetime DEFAULT NULL,
  `must_change_password` tinyint(1) NOT NULL,
  `department_id` int DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  `created_by_user_id` int DEFAULT NULL,
  `updated_by_user_id` int DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted_by_user_id` int DEFAULT NULL,
  `version` int NOT NULL,
  `locked_until` datetime DEFAULT NULL,
  `session_version` int NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_users_username` (`username`),
  UNIQUE KEY `ix_users_email` (`email`),
  UNIQUE KEY `ix_users_employee_number` (`employee_number`),
  KEY `fk_users_department` (`department_id`),
  CONSTRAINT `fk_users_department` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO `users` (username, email, password_hash, employee_number, first_name, last_name, phone, extension, is_active, is_locked, locked_at, lock_reason, last_login_at, last_login_ip, failed_login_attempts, last_failed_login_at, password_changed_at, must_change_password, department_id, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id, version, locked_until, session_version) VALUES ("admin", "admin@hospital.local", "scrypt:32768:8:1$IafMeKFZGH24raC1$6de40922609bb216d65576ea13288f9b7a78aa42e4e3cad2d0c523559ef347c0013ba9e10923bcf6781e7f46aa57bff4a860fc108373549174a7b583eca6150b", "ADMIN001", "System", "Administrator", NULL, NULL, 1, 0, NULL, NULL, datetime.datetime(2026, 11, 19, 15, 3, 47), "127.0.0.1", 0, NULL, datetime.datetime(2026, 11, 16, 6, 40, 18), 0, 1, 1, datetime.datetime(2026, 11, 16, 6, 40, 18), datetime.datetime(2026, 11, 19, 15, 3, 47), NULL, NULL, NULL, NULL, 1, datetime.datetime(2026, 11, 16, 8, 26, 23), 1);
INSERT INTO `users` (username, email, password_hash, employee_number, first_name, last_name, phone, extension, is_active, is_locked, locked_at, lock_reason, last_login_at, last_login_ip, failed_login_attempts, last_failed_login_at, password_changed_at, must_change_password, department_id, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id, version, locked_until, session_version) VALUES ("helpdesk", "helpdesk@hospital.local", "scrypt:32768:8:1$2YJEFR7fBHjaiYGn$c147003f567b531228ff142679ee35d21a9b7737e5a3b8ca0bb391ecdaf459603611aa3b7b2aaf06b4e2933f7ae1aed2247873711b4119e874304cc72664c96e", "HD001", "Helpdesk", "Agent", NULL, NULL, 1, 0, NULL, NULL, datetime.datetime(2026, 11, 19, 7, 46, 25), "127.0.0.1", 0, NULL, datetime.datetime(2026, 11, 16, 6, 40, 18), 0, 1, 2, datetime.datetime(2026, 11, 16, 6, 40, 18), datetime.datetime(2026, 11, 19, 7, 46, 25), NULL, NULL, NULL, NULL, 1, NULL, 1);
INSERT INTO `users` (username, email, password_hash, employee_number, first_name, last_name, phone, extension, is_active, is_locked, locked_at, lock_reason, last_login_at, last_login_ip, failed_login_attempts, last_failed_login_at, password_changed_at, must_change_password, department_id, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id, version, locked_until, session_version) VALUES ("support", "support@hospital.local", "scrypt:32768:8:1$HUys7k4Gh1dOEluK$3c3cb384f585882e9a07dd99a599e4a2104b66512e2decba0ea6462e14b827c3e668b4248333cca17ab1a1a2a4db0547359871f8bb53999933ad5842c854ab67", "SA001", "Support", "Agent", NULL, NULL, 1, 0, NULL, NULL, datetime.datetime(2026, 11, 19, 7, 52, 9), "127.0.0.1", 0, NULL, datetime.datetime(2026, 11, 19, 7, 52, 43), 0, 1, 3, datetime.datetime(2026, 11, 16, 6, 40, 18), datetime.datetime(2026, 11, 19, 7, 52, 43), NULL, NULL, NULL, NULL, 1, NULL, 2);
INSERT INTO `users` (username, email, password_hash, employee_number, first_name, last_name, phone, extension, is_active, is_locked, locked_at, lock_reason, last_login_at, last_login_ip, failed_login_attempts, last_failed_login_at, password_changed_at, must_change_password, department_id, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id, version, locked_until, session_version) VALUES ("user", "user@hospital.local", "scrypt:32768:8:1$jkYiWl3fqwznFcHA$23b7a556132c116dd0df2f5d6a46f977cb6426892db20b2354b2f79d266de3024251f50cdd1104d1be09e5d61a71965553dd4812fe84ae502f55805f1a28661c", "USR001", "Hospital", "User", NULL, NULL, 1, 0, NULL, NULL, datetime.datetime(2026, 11, 19, 7, 53, 29), "127.0.0.1", 0, NULL, datetime.datetime(2026, 11, 19, 7, 50, 46), 0, 4, 4, datetime.datetime(2026, 11, 16, 6, 40, 18), datetime.datetime(2026, 11, 19, 7, 53, 29), NULL, NULL, NULL, NULL, 1, NULL, 2);
INSERT INTO `users` (username, email, password_hash, employee_number, first_name, last_name, phone, extension, is_active, is_locked, locked_at, lock_reason, last_login_at, last_login_ip, failed_login_attempts, last_failed_login_at, password_changed_at, must_change_password, department_id, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id, version, locked_until, session_version) VALUES ("demo_helpdesk", "demo_helpdesk@example.local", "scrypt:32768:8:1$KgI9crYwUCZ2Ygze$02803d02977d8014f8dc4558444ff002aca7b61f52b0df505282cb3f0b58d8f35b9005a91dff22e85a03eee37703030d6e3932e65dc7e18c4659376df27ae1f2", "DHD001", "Demo", "Helpdesk", NULL, NULL, 1, 0, NULL, NULL, NULL, NULL, 0, NULL, datetime.datetime(2026, 11, 16, 6, 59), 0, 1, 5, datetime.datetime(2026, 11, 16, 6, 59), datetime.datetime(2026, 11, 16, 6, 59), NULL, NULL, NULL, NULL, 1, NULL, 1);
INSERT INTO `users` (username, email, password_hash, employee_number, first_name, last_name, phone, extension, is_active, is_locked, locked_at, lock_reason, last_login_at, last_login_ip, failed_login_attempts, last_failed_login_at, password_changed_at, must_change_password, department_id, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id, version, locked_until, session_version) VALUES ("demo_support", "demo_support@example.local", "scrypt:32768:8:1$txTokQI81DY6u129$128c3ccf74c2c541e32ae02ed65fcf75b19ebcc0a1e53a6bf8c2f04c3ef61d42f7e630a5494d0848c31d8364956720be38bc6dcc8f8936bb4a855973d807bf06", "DSP001", "Demo", "Support", NULL, NULL, 1, 0, NULL, NULL, datetime.datetime(2026, 11, 16, 8, 43, 45), "127.0.0.1", 0, NULL, datetime.datetime(2026, 11, 16, 6, 59, 1), 0, 1, 6, datetime.datetime(2026, 11, 16, 6, 59, 1), datetime.datetime(2026, 11, 16, 8, 43, 45), NULL, NULL, NULL, NULL, 1, NULL, 1);
INSERT INTO `users` (username, email, password_hash, employee_number, first_name, last_name, phone, extension, is_active, is_locked, locked_at, lock_reason, last_login_at, last_login_ip, failed_login_attempts, last_failed_login_at, password_changed_at, must_change_password, department_id, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id, version, locked_until, session_version) VALUES ("demo_user", "demo_user@example.local", "scrypt:32768:8:1$J3p7HB2xYwhqDMtM$8ce61fe86f63b027dba8bb9a7debbd8ab507e6aa6c0186216ba4b63ab8a14ed0eb449fdf2c5f92feaf07dbdb4d45bd2052d7f8f0ca1a0cff7e34f875f3d2ebef", "DUS001", "Demo", "Reporter", NULL, NULL, 1, 0, NULL, NULL, NULL, NULL, 0, NULL, datetime.datetime(2026, 11, 16, 6, 59, 1), 0, 4, 7, datetime.datetime(2026, 11, 16, 6, 59, 1), datetime.datetime(2026, 11, 16, 6, 59, 1), NULL, NULL, NULL, NULL, 1, NULL, 1);
-- Table: working_schedules
-- Row count: 1
CREATE TABLE `working_schedules` (
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `timezone` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `weekly_schedule` json NOT NULL,
  `exceptions` json DEFAULT NULL,
  `department_id` int DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `is_default` tinyint(1) NOT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  `created_by_user_id` int DEFAULT NULL,
  `updated_by_user_id` int DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted_by_user_id` int DEFAULT NULL,
  `version` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_working_schedules_name` (`name`),
  KEY `fk_working_schedules_department_id_departments` (`department_id`),
  CONSTRAINT `fk_working_schedules_department_id_departments` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO `working_schedules` (name, description, timezone, weekly_schedule, exceptions, department_id, is_active, is_default, id, created_at, updated_at, created_by_user_id, updated_by_user_id, deleted_at, deleted_by_user_id, version) VALUES ("Standard Business Hours", "Monday-Friday, 09:00-17:00 Pakistan time", "Asia/Karachi", "{\"0\": {\"end\": \"17:00\", \"start\": \"09:00\"}, \"1\": {\"end\": \"17:00\", \"start\": \"09:00\"}, \"2\": {\"end\": \"17:00\", \"start\": \"09:00\"}, \"3\": {\"end\": \"17:00\", \"start\": \"09:00\"}, \"4\": {\"end\": \"17:00\", \"start\": \"09:00\"}, \"5\": null, \"6\": null}", "{}", NULL, 1, 1, 1, datetime.datetime(2026, 11, 16, 6, 40, 18), datetime.datetime(2026, 11, 16, 6, 40, 18), NULL, NULL, NULL, NULL, 1);
-- End of backup

create database if not exists payview;
use payview;
CREATE TABLE shops (shop_id int auto_increment, name VARCHAR(255) NOT NULL , latitude DOUBLE NOT NULL, longitude DOUBLE NOT NULL, PRIMARY KEY (shop_id), UNIQUE KEY (name));
CREATE TABLE payment_groups (group_id CHAR(4) NOT NULL, group_name VARCHAR(255) NOT NULL, PRIMARY KEY (group_id), UNIQUE KEY (group_name));
create table payment_services (payment_id CHAR(4) not null, name VARCHAR(255) not null, payment_group CHAR(4) not null,PRIMARY KEY (payment_id), UNIQUE KEY (name), FOREIGN KEY (payment_group) REFERENCES payment_groups(group_id) on update cascade);
create table tags (tag_id CHAR(4) not null, name VARCHAR(255) not null, PRIMARY KEY (tag_id), UNIQUE KEY (name));
create table can_use_services (shop_id int not null, payment_id CHAR(4) not null, foreign key fk_shop_id (shop_id)REFERENCES shops (shop_id) ON DELETE CASCADE, foreign key fk_payment_id (payment_id) REFERENCES payment_services (payment_id) ON DELETE CASCADE, PRIMARY KEY(shop_id,payment_id));
create table allocated_tags (shop_id int not null, tag_id CHAR(4) not null, foreign key fk_shop_id (shop_id) REFERENCES shops (shop_id) ON DELETE CASCADE, foreign key fk_tag_id (tag_id) REFERENCES tags (tag_id) ON DELETE CASCADE, PRIMARY KEY(shop_id, tag_id));
CREATE TABLE payment_schemes (payment_id CHAR(4) NOT NULL, iOS_scheme VARCHAR(255), Android_scheme VARCHAR(255), FOREIGN KEY (payment_id) REFERENCES payment_services(payment_id) on delete cascade on update cascade);

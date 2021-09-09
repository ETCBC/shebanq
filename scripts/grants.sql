GRANT SELECT ON `shebanq\_etcbc%`.* TO 'shebanq'@'localhost';
GRANT SELECT ON `shebanq\_passage%`.* TO 'shebanq'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER ON shebanq_web.* TO 'shebanq'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER ON shebanq_note.* TO 'shebanq'@'localhost';

GRANT USAGE ON *.* TO 'shebanq_admin'@'localhost';
GRANT ALL PRIVILEGES ON `shebanq%`.* TO 'shebanq_admin'@'localhost' WITH GRANT OPTION; 

FLUSH PRIVILEGES;

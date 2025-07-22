CREATE TABLE IF NOT EXISTS alunos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    matricula VARCHAR(50) NOT NULL UNIQUE,
    data_nascimento DATE NOT NULL,
    curso VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS registros_refeitorio (
    id INT AUTO_INCREMENT PRIMARY KEY,
    aluno_id INT NOT NULL,
    foto LONGBLOB,
    hora_entrada DATETIME,
    hora_saida DATETIME,
    FOREIGN KEY (aluno_id) REFERENCES alunos(id)
); 
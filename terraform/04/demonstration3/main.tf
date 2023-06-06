terraform{

}
provider "vault" {
    address = "http://127.0.0.1:8200"
    skip_tls_verify = true
    token = "education"
        # checkov:skip=CKV_SECRET_6: education
}

data "vault_generic_secret" "vault_example"{
 path = "secret/example"
}
output "vault_example" {
 value = "${nonsensitive(data.vault_generic_secret.vault_example.data.1)}" #функция nonsensitive позволяет узнать значение sensitive данных
} 

#содержимое секретное. поглядеть можно через консоль

#> data.vault_generic_secret.vault_example # а содержимое data то скрыто!


#> nonsensitive(data.vault_generic_secret.vault_example.data) #вот так можно подсмотреть все ключи и значения

#> nonsensitive(data.vault_generic_secret.vault_example.data).1 а вот так сожно извлечь конкретный ключ

#Чем хорош vault ? Это версионирование для секретов.

terraform state list

terraform state show 'yandex_vpc_network.develop'

terraform state show 'module.test-vm.yandex_compute_instance.vm[0]'

terraform apply -target module.test-vm

terraform apply -target module.test-vm -replace='module.test-vm.yandex_compute_instance.vm[0]'

terraform state show 'module.test-vm.yandex_compute_instance.vm[0]' | grep 'id'

terraform state rm 'module.test-vm.yandex_compute_instance.vm[0]'

terraform import 'module.test-vm.yandex_compute_instance.vm[0]' fhm1g61rfod251rpdeqg #<VM.ID>
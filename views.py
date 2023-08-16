from datetime import datetime

from rest_framework.response import Response  # Импорты классов
from rest_framework.views import APIView

from .models import PermittedUser, StateUser


# Create your views here.
class UserAccessView(APIView):  # класс который работает с запросами
    @staticmethod
    def get_client_ip(request):  # ф-ция определяющая ip адресс с которого пробросили запрос
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')  # request отвечает за данные с запроса
        if x_forwarded_for:  # мета отвечает за данные в запросе
            ip = x_forwarded_for.split(',')[0].strip()  # разбивает ip адресс по запятой и берёт 1й элемент
        else:  # а также удаляет пробелы до и после строки
            ip = request.META.get('REMOTE_ADDR')
        return ip  # возращает ip адресс из ф-ции

    @staticmethod  # указывает на то, что метод статический (не использует внутри себя self)
    def state_user(request, client_ip):
        # пытаемся получить пользователя по username и hostname
        try:
            return StateUser.objects.get(username=request.data["username"], hostname=request.data["hostname"])
        # если не нашли, то создаём
        except StateUser.DoesNotExist:
            return StateUser.objects.create(
                username=request.data["username"],
                userdomain=request.data["userdomain"],
                hostname=request.data["hostname"],
                ipaddress=request.data["ipaddress"],
                type_of_service=request.data["logontype"],
                localdatetime=datetime.strptime(request.data["localdatetime"], "%Y-%m-%d %H:%M:%S"),
                session_ip=client_ip,
                status="active"
            )

    def post(self, request, *args, **kwargs):  # ф-ция Post обрабатывает все входящие post запросы
        client_ip = self.get_client_ip(request)
        type_request = request.data['type'].split()[-1]
        # Получаем тип входа из запроса. Разбиваем по пробелам и берем последний элемент
        # (потому что в последнем элементе лежит ключевое слово)
        PermittedUser.objects.create(  # создаём запись в таблице PermittedUser
            username=request.data["username"],
            userdomain=request.data["userdomain"],
            hostname=request.data["hostname"],
            ipaddress=request.data["ipaddress"],
            type_of_service=request.data["logontype"],
            localdatetime=datetime.strptime(request.data["localdatetime"], "%Y-%m-%d %H:%M:%S"),
            session_ip=client_ip,
        )
        if type_request == 'logon':
            self.state_user(request, client_ip)
            # Либо получаем такого пользователя, либо создаём
        elif type_request == 'logoff':
            self.state_user(request, client_ip).delete()
            # Получаем такого пользователя и удаляем
        elif type_request == 'lock':
            user = self.state_user(request, client_ip)
            user.state = "locked"
            user.save()
            # Получаем такого пользователя и меняем state на locked
        elif type_request == 'unlock':
            user = self.state_user(request, client_ip)
            user.state = "active"
            user.save()
            # Получаем такого пользователя и меняем state на active
        elif type_request == 'disconnect':
            user = self.state_user(request, client_ip)
            user.state = "disconnect"
            user.save()
            # Получаем такого пользователя и меняем state на disconnect
        elif type_request == 'reconnect':
            user = self.state_user(request, client_ip)
            user.state = "active"
            user.save()
            # Получаем такого пользователя и меняем state на active
        elif type_request == 'powerOFF':
            users = StateUser.objects.filter(
                hostname=request.data["hostname"],
                localdatetime__lte=datetime.strptime(request.data["localdatetime"], "%Y-%m-%d %H:%M:%S")
            )
            for user in users:
                user.delete()
            # Получаем всех пользователей по hostname
            # localdatetime__lte (время меньше или равно) localdatetime события выключения и удаляем такие записи
        return Response("Insert done")  # возвращяем пользователю сообщение

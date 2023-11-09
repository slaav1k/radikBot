from telegram.ext import Updater, CommandHandler, CallbackContext
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone

import generationData
import tokenBot


def falc_start_lesson(context: CallbackContext):
    lesson_time, lesson_name, chat_id = context.job.context
    context.bot.send_message(chat_id, f"Через 10 минут начало пары:\n{lesson_time} - {lesson_name}")


# Функция для отправки сообщения о начале пары
def start_lesson(context: CallbackContext):
    lesson_time, lesson_name, chat_id = context.job.context
    context.bot.send_message(chat_id, f"Начало пары: {lesson_time} - {lesson_name}")


def peremena_lesson(context: CallbackContext):
    lesson_time, lesson_name, chat_id = context.job.context
    context.bot.send_message(chat_id, f"Перерыв 5 минут")


# Функция для отправки сообщения о конце пары
def end_lesson(context: CallbackContext):
    lesson_time, lesson_name, chat_id = context.job.context
    context.bot.send_message(chat_id, f"Конец пары: {lesson_time} - {lesson_name}")


# Функция для установки уведомлений
def set_lesson_notification(update, context):
    # lesson_data = ['9:53 - 9:54', 'Лек. Архитектура выч. систем 206-1']  # Замените на реальные данные
    data = generationData.generate_data()
    for lesson_data in data:

        lesson_time, lesson_name = lesson_data
        chat_id = update.message.chat_id

        # Парсим время начала и окончания пары
        start_time, end_time = map(lambda x: datetime.strptime(x, '%H:%M'), lesson_time.split(' - '))
        start_time = start_time.replace(year=datetime.now().year,
                                        month=datetime.now().month,
                                        day=datetime.now().day,
                                        second=0,
                                        microsecond=0)
        falc_start_time = start_time - timedelta(minutes=10)
        peremena_time = start_time + timedelta(minutes=45)
        end_time = end_time.replace(year=datetime.now().year,
                                    month=datetime.now().month,
                                    day=datetime.now().day,
                                    second=0,
                                    microsecond=0)
        print(start_time, peremena_time, end_time)

        # Вычисляем разницу во времени между текущим временем и началом пары
        time_until_start = (start_time - datetime.now()).total_seconds()
        print("time_until_start", time_until_start)

        time_until_peremena = (peremena_time - datetime.now()).total_seconds()
        time_until_falc = (falc_start_time - datetime.now()).total_seconds()
        print("time_until_peremena", time_until_peremena)

        # Вычисляем разницу во времени между текущим временем и окончанием пары
        time_until_end = (end_time - datetime.now()).total_seconds()
        print("time_until_end", time_until_end)

        # Устанавливаем уведомление о начале пары
        context.job_queue.run_once(start_lesson, time_until_start, context=(lesson_time, lesson_name, chat_id))

        context.job_queue.run_once(peremena_lesson, time_until_peremena, context=(lesson_time, lesson_name, chat_id))
        context.job_queue.run_once(falc_start_lesson, time_until_falc, context=(lesson_time, lesson_name, chat_id))

        # Устанавливаем уведомление о конце пары
        context.job_queue.run_once(end_lesson, time_until_end, context=(lesson_time, lesson_name, chat_id))

        update.message.reply_text(f"Уведомления установлены для пары: {lesson_time} - {lesson_name}")
    if not data:
        update.message.reply_text(f"Выходной")


def main():
    updater = Updater(token=tokenBot.TOKEN_BOT, use_context=True)
    dp = updater.dispatcher

    # Добавляем обработчики команд
    dp.add_handler(CommandHandler('start', set_lesson_notification))

    tz = timezone('Europe/Moscow')
    scheduler = BackgroundScheduler()
    scheduler.add_job(set_lesson_notification, 'cron', hour=0, minute=0, args=(None, updater.job_queue), timezone=tz)
    scheduler.start()

    # Запускаем бота
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

#
# subprocess.run(['python', '-m', 'ensurepip', '--default-pip'])
# subprocess.run(['pip', 'install', 'python-telegram-bot~=13.4.1'])
# subprocess.run(["pip", "install", "pytz"])
# subprocess.run(["pip", "install", "apscheduler"])

from datetime import datetime, timedelta, time

from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext

import generationData
import tokenBot

scheduler = BackgroundScheduler()
keys_board = [['/start'], ['/lessons'], ['/check']]
markup = ReplyKeyboardMarkup(keys_board, one_time_keyboard=True)


def falc_start_lesson(context: CallbackContext):
    lesson_time, lesson_name, chat_id = context.job.context
    context.bot.send_message(
        chat_id,
        f"Через 10 минут начало пары:\n{lesson_time} - {lesson_name}",
        reply_markup=markup)


# Функция для отправки сообщения о начале пары
def start_lesson(context: CallbackContext):
    lesson_time, lesson_name, chat_id = context.job.context
    context.bot.send_message(chat_id,
                             f"Начало пары: {lesson_time} - {lesson_name}",
                             reply_markup=markup)


def peremena_lesson(context: CallbackContext):
    lesson_time, lesson_name, chat_id = context.job.context
    context.bot.send_message(chat_id, f"Перерыв 5 минут", reply_markup=markup)


# Функция для отправки сообщения о конце пары
def end_lesson(context: CallbackContext):
    lesson_time, lesson_name, chat_id = context.job.context
    context.bot.send_message(chat_id,
                             f"Конец пары: {lesson_time} - {lesson_name}",
                             reply_markup=markup)


def check_status_bot(update, context):
    update.message.reply_text(f"Я живой", reply_markup=markup)


def lessons(update, context):
    data = generationData.generate_data()
    for lesson_data in data:
        lesson_time, lesson_name = lesson_data
        update.message.reply_text(f"{lesson_time} - {lesson_name}",
                                  reply_markup=markup)
    if not data:
        update.message.reply_text(f"Выходной", reply_markup=markup)


def set_lesson_notification_command(context: CallbackContext):
    chat_id = context.job.context
    data = generationData.generate_data()
    for lesson_data in data:
        lesson_time, lesson_name = lesson_data

        # Парсим время начала и окончания пары
        start_time, end_time = map(lambda x: datetime.strptime(x, '%H:%M'),
                                   lesson_time.split())
        start_time = start_time.replace(year=datetime.now().year,
                                        month=datetime.now().month,
                                        day=datetime.now().day,
                                        second=0,
                                        microsecond=0)
        # start_time = start_time - timedelta(hours=3)
        falc_start_time = start_time - timedelta(minutes=10)
        peremena_time = start_time + timedelta(minutes=45)
        end_time = end_time.replace(year=datetime.now().year,
                                    month=datetime.now().month,
                                    day=datetime.now().day,
                                    second=0,
                                    microsecond=0)
        # end_time = end_time - timedelta(hours=3)
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
        context.job_queue.run_once(start_lesson,
                                   time_until_start,
                                   context=(lesson_time, lesson_name, chat_id))

        context.job_queue.run_once(peremena_lesson,
                                   time_until_peremena,
                                   context=(lesson_time, lesson_name, chat_id))
        context.job_queue.run_once(falc_start_lesson,
                                   time_until_falc,
                                   context=(lesson_time, lesson_name, chat_id))

        # Устанавливаем уведомление о конце пары
        context.job_queue.run_once(end_lesson,
                                   time_until_end,
                                   context=(lesson_time, lesson_name, chat_id))

        context.bot.send_message(
            chat_id,
            f"Уведомления установлены для пары: {lesson_time} - {lesson_name}",
            reply_markup=markup)
    if not data:
        context.bot.send_message(chat_id, f"Выходной", reply_markup=markup)


# Функция для установки уведомлений
def set_lesson_notification(update, context):
    chat_id = update.message.chat_id
    print(datetime.now())

    filtered_jobs = [job for job in context.job_queue.jobs() if str(chat_id) in job.name]
    for job in filtered_jobs:
        job.schedule_removal()

    # context.bot.send_message(chat_id, f"{datetime.now()}")
    context.job_queue.run_daily(set_lesson_notification_command,
                                time=time(hour=4, minute=00),
                                context=chat_id, name=f"set_lesson_{chat_id}")

    context.job_queue.run_once(set_lesson_notification_command,
                               1,
                               context=chat_id, name=f"set_lesson_{chat_id}")

    # context.job_queue.run_repeating(set_lesson_notification_command,
    #                                 interval=60 * 60 * 24,
    #                                 first=1,
    #                                 context=chat_id)

    # context.job_queue.run_repeating(set_lesson_notification_command,
    #                                 interval=5,
    #                                 first=1,
    #                                 context=chat_id)
    print([job for job in context.job_queue.jobs() if str(chat_id) in job.name])
    # filtered_jobs = [job for job in context.job_queue.jobs() if str(chat_id) in job.name]


def main():
    updater = Updater(token=tokenBot.TOKEN_BOT, use_context=True)
    dp = updater.dispatcher

    # Добавляем обработчики команд
    dp.add_handler(CommandHandler('start', set_lesson_notification))
    dp.add_handler(CommandHandler('check', check_status_bot))
    dp.add_handler(CommandHandler('lessons', lessons))

    tz = timezone('Europe/Moscow')
    scheduler = BackgroundScheduler()
    scheduler.add_job(set_lesson_notification,
                      'cron',
                      hour=0,
                      minute=20,
                      args=(None, updater.job_queue),
                      timezone=tz)
    scheduler.start()

    # Запускаем бота
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

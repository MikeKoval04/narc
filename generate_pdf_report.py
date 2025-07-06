#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор PDF отчетов из JSON файлов чатов бота.
Создает PDF файл со всеми диалогами в хронологическом порядке.
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.pdfbase import pdfutils
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


def register_fonts():
    """Регистрируем шрифты для поддержки русского языка"""
    try:
        # Пытаемся зарегистрировать системные шрифты
        font_paths = [
            '/System/Library/Fonts/Arial.ttf',  # macOS
            '/System/Library/Fonts/Helvetica.ttc',  # macOS
            'C:/Windows/Fonts/arial.ttf',  # Windows
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',  # Linux
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('CustomFont', font_path))
                    return 'CustomFont'
                except:
                    continue
        
        # Если не удалось зарегистрировать шрифт, используем встроенный
        return 'Helvetica'
    except:
        return 'Helvetica'


def clean_text(text: str) -> str:
    """Очищает текст от HTML тегов и специальных символов"""
    # Удаляем HTML теги
    text = re.sub(r'<[^>]+>', '', text)
    # Заменяем HTML entities
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    return text


def load_chat_files(chats_dir: str) -> list:
    """Загружает все JSON файлы чатов и сортирует их по времени создания"""
    chat_files = []
    
    if not os.path.exists(chats_dir):
        print(f"Папка {chats_dir} не существует")
        return []
    
    for filename in os.listdir(chats_dir):
        if filename.endswith('.json') and filename.startswith('chat_'):
            filepath = os.path.join(chats_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Получаем время первого сообщения для сортировки
                if data.get('messages'):
                    first_timestamp = data['messages'][0].get('timestamp', '')
                    chat_files.append({
                        'filename': filename,
                        'filepath': filepath,
                        'data': data,
                        'first_timestamp': first_timestamp
                    })
            except Exception as e:
                print(f"Ошибка при загрузке {filename}: {e}")
    
    # Сортируем по времени первого сообщения
    chat_files.sort(key=lambda x: x['first_timestamp'])
    return chat_files


def format_timestamp(timestamp_str: str) -> str:
    """Форматирует timestamp в читаемый вид"""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime('%d.%m.%Y %H:%M:%S')
    except:
        return timestamp_str


def create_styles(font_name: str):
    """Создает стили для PDF документа"""
    styles = getSampleStyleSheet()
    
    # Стиль для заголовка чата
    chat_title_style = ParagraphStyle(
        'ChatTitle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=16,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor='#2E86AB'
    )
    
    # Стиль для сообщений пользователя (справа)
    user_message_style = ParagraphStyle(
        'UserMessage',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=11,
        alignment=TA_RIGHT,
        leftIndent=4*cm,
        rightIndent=0.5*cm,
        spaceBefore=8,
        spaceAfter=8,
        borderWidth=1,
        borderColor='#E3F2FD',
        backColor='#E3F2FD',
        borderPadding=8,
        borderRadius=8
    )
    
    # Стиль для сообщений ассистента (слева)
    assistant_message_style = ParagraphStyle(
        'AssistantMessage',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=11,
        alignment=TA_LEFT,
        leftIndent=0.5*cm,
        rightIndent=4*cm,
        spaceBefore=8,
        spaceAfter=8,
        borderWidth=1,
        borderColor='#F3E5F5',
        backColor='#F3E5F5',
        borderPadding=8,
        borderRadius=8
    )
    
    # Стиль для метки времени
    timestamp_style = ParagraphStyle(
        'Timestamp',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=8,
        textColor='#666666',
        spaceBefore=2,
        spaceAfter=6
    )
    
    # Стиль для системных сообщений
    system_message_style = ParagraphStyle(
        'SystemMessage',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        alignment=TA_CENTER,
        textColor='#888888',
        spaceBefore=8,
        spaceAfter=8,
        fontStyle='italic'
    )
    
    return {
        'chat_title': chat_title_style,
        'user_message': user_message_style,
        'assistant_message': assistant_message_style,
        'timestamp': timestamp_style,
        'system_message': system_message_style
    }


def generate_pdf_report(chats_dir: str = 'chats', output_file: str = 'chat_report.pdf'):
    """Генерирует PDF отчет из всех чатов"""
    
    print("Начинаем генерацию PDF отчета...")
    
    # Регистрируем шрифты
    font_name = register_fonts()
    print(f"Используем шрифт: {font_name}")
    
    # Загружаем файлы чатов
    chat_files = load_chat_files(chats_dir)
    if not chat_files:
        print("Не найдено файлов чатов для обработки")
        return
    
    print(f"Найдено {len(chat_files)} файлов чатов")
    
    # Создаем PDF документ
    doc = SimpleDocTemplate(
        output_file,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Создаем стили
    styles = create_styles(font_name)
    
    # Создаем содержимое документа
    story = []
    
    # Заголовок документа
    title = Paragraph(
        f"Отчет по диалогам психологического симулятора<br/>Сгенерирован: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
        styles['chat_title']
    )
    story.append(title)
    story.append(Spacer(1, 1*cm))
    
    # Обрабатываем каждый файл чата
    for i, chat_file in enumerate(chat_files):
        print(f"Обрабатываем файл {i+1}/{len(chat_files)}: {chat_file['filename']}")
        
        data = chat_file['data']
        chat_id = data.get('chat_id', 'Unknown')
        messages = data.get('messages', [])
        
        if not messages:
            continue
        
        # Заголовок чата
        chat_title = Paragraph(
            f"Чат {chat_id} ({chat_file['filename']})",
            styles['chat_title']
        )
        story.append(chat_title)
        story.append(Spacer(1, 0.5*cm))
        
        # Обрабатываем сообщения
        for msg in messages:
            role = msg.get('role', '')
            content = msg.get('content', '')
            timestamp = msg.get('timestamp', '')
            
            # Очищаем контент от HTML тегов
            clean_content = clean_text(content)
            
            # Пропускаем пустые сообщения
            if not clean_content.strip():
                continue
            
            # Форматируем timestamp
            formatted_time = format_timestamp(timestamp)
            
            if role == 'user':
                # Сообщение пользователя (справа)
                timestamp_para = Paragraph(
                    f"👤 Психолог - {formatted_time}",
                    styles['timestamp']
                )
                timestamp_para.hAlign = 'RIGHT'
                story.append(timestamp_para)
                
                message_para = Paragraph(clean_content, styles['user_message'])
                story.append(message_para)
                
            elif role == 'assistant':
                # Сообщение ассистента (слева)
                timestamp_para = Paragraph(
                    f"🤖 Клиент - {formatted_time}",
                    styles['timestamp']
                )
                timestamp_para.hAlign = 'LEFT'
                story.append(timestamp_para)
                
                message_para = Paragraph(clean_content, styles['assistant_message'])
                story.append(message_para)
                
            elif role == 'system':
                # Системное сообщение
                if 'История диалога очищена' not in content:  # Пропускаем уведомления об очистке
                    system_para = Paragraph(
                        f"🔧 Система - {formatted_time}: {clean_content}",
                        styles['system_message']
                    )
                    story.append(system_para)
            
            story.append(Spacer(1, 0.2*cm))
        
        # Разделитель между чатами (кроме последнего)
        if i < len(chat_files) - 1:
            story.append(PageBreak())
    
    # Генерируем PDF
    print("Создаем PDF файл...")
    doc.build(story)
    print(f"PDF отчет сохранен как: {output_file}")


def main():
    """Основная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Генерация PDF отчета из чатов бота')
    parser.add_argument('--chats-dir', default='chats', help='Папка с JSON файлами чатов')
    parser.add_argument('--output', default='chat_report.pdf', help='Имя выходного PDF файла')
    
    args = parser.parse_args()
    
    try:
        generate_pdf_report(args.chats_dir, args.output)
        print("✅ Генерация PDF отчета завершена успешно!")
    except Exception as e:
        print(f"❌ Ошибка при генерации PDF: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

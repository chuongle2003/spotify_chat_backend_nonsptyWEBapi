from django.core.management.base import BaseCommand, CommandError
import os
import sys
import importlib.util
import traceback

class Command(BaseCommand):
    help = 'Tạo dữ liệu giả lập toàn diện cho hệ thống nhạc'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            help='Loại dữ liệu cần tạo: trending, activity, playlists, all',
            default='all'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Bỏ qua xác nhận và tạo dữ liệu ngay lập tức',
        )

    def handle(self, *args, **options):
        data_type = options['type']
        force = options['force']
        
        # Hiển thị thông tin
        self.stdout.write(self.style.SUCCESS('=== CÔNG CỤ TẠO DỮ LIỆU GIẢ LẬP CHO HỆ THỐNG ÂM NHẠC ==='))
        
        # Kiểm tra và yêu cầu xác nhận nếu không dùng --force
        if not force:
            self.stdout.write(self.style.WARNING(
                'CẢNH BÁO: Quá trình này sẽ tạo nhiều dữ liệu trong database hiện tại.\n'
                'Nó có thể thay đổi dữ liệu hiện có và làm chậm hệ thống trong quá trình chạy.\n'
                'Bạn nên sao lưu database trước khi tiếp tục.'
            ))
            
            confirm = input('\nBạn có chắc chắn muốn tiếp tục? (y/N): ')
            if confirm.lower() != 'y':
                self.stdout.write(self.style.ERROR('Đã hủy tạo dữ liệu.'))
                return
        
        # Chạy script tạo dữ liệu dựa trên loại
        try:
            if data_type == 'all' or data_type == 'trending':
                self.generate_trending_data()
            
            if data_type == 'all' or data_type == 'activity':
                self.generate_realistic_activity()
            
            if data_type == 'all' or data_type == 'playlists':
                self.generate_realistic_playlists()
            
            self.stdout.write(self.style.SUCCESS('Đã hoàn thành việc tạo dữ liệu giả lập!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Lỗi trong quá trình tạo dữ liệu: {str(e)}'))
            traceback.print_exc()
    
    def generate_trending_data(self):
        """Tạo dữ liệu trending"""
        self.stdout.write(self.style.NOTICE('\n=== ĐANG TẠO DỮ LIỆU TRENDING ==='))
        
        try:
            # Tải module từ file python
            module_path = os.path.join(os.path.dirname(__file__), 'generate_trending_data.py')
            if not os.path.exists(module_path):
                self.stdout.write(self.style.ERROR(f'Không tìm thấy file module: {module_path}'))
                return
                
            spec = importlib.util.spec_from_file_location("generate_trending_data", module_path)
            if spec is None or spec.loader is None:
                self.stdout.write(self.style.ERROR(f'Không thể tải module từ file: {module_path}'))
                return
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Gọi hàm tạo dữ liệu trending
            module.generate_trending_data()
            
            self.stdout.write(self.style.SUCCESS('✓ Đã tạo dữ liệu trending thành công'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Lỗi khi tạo dữ liệu trending: {str(e)}'))
            raise
    
    def generate_realistic_activity(self):
        """Tạo dữ liệu hoạt động thực tế"""
        self.stdout.write(self.style.NOTICE('\n=== ĐANG TẠO DỮ LIỆU HOẠT ĐỘNG THỰC TẾ ==='))
        
        try:
            # Tải module từ file python
            module_path = os.path.join(os.path.dirname(__file__), 'generate_realistic_activity.py')
            if not os.path.exists(module_path):
                self.stdout.write(self.style.ERROR(f'Không tìm thấy file module: {module_path}'))
                return
                
            spec = importlib.util.spec_from_file_location("generate_realistic_activity", module_path)
            if spec is None or spec.loader is None:
                self.stdout.write(self.style.ERROR(f'Không thể tải module từ file: {module_path}'))
                return
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Khởi tạo và chạy generator
            generator = module.RealisticActivityGenerator()
            generator.run()
            
            self.stdout.write(self.style.SUCCESS('✓ Đã tạo dữ liệu hoạt động thực tế thành công'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Lỗi khi tạo dữ liệu hoạt động: {str(e)}'))
            raise
    
    def generate_realistic_playlists(self):
        """Tạo dữ liệu playlist thực tế"""
        self.stdout.write(self.style.NOTICE('\n=== ĐANG TẠO DỮ LIỆU PLAYLIST THỰC TẾ ==='))
        
        try:
            # Tải module từ file python
            module_path = os.path.join(os.path.dirname(__file__), 'generate_realistic_playlists.py')
            if not os.path.exists(module_path):
                self.stdout.write(self.style.ERROR(f'Không tìm thấy file module: {module_path}'))
                return
                
            spec = importlib.util.spec_from_file_location("generate_realistic_playlists", module_path)
            if spec is None or spec.loader is None:
                self.stdout.write(self.style.ERROR(f'Không thể tải module từ file: {module_path}'))
                return
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Khởi tạo và chạy generator
            generator = module.RealisticPlaylistGenerator()
            generator.run()
            
            self.stdout.write(self.style.SUCCESS('✓ Đã tạo dữ liệu playlist thực tế thành công'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Lỗi khi tạo dữ liệu playlist: {str(e)}'))
            raise 
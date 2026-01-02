"""Test script to verify download progress tracking."""

import threading
from tqdm import tqdm
import tqdm as tqdm_module
from huggingface_hub import hf_hub_download, HfApi
import tempfile

def _format_bytes(bytes_val: int) -> str:
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.1f} KB"
    elif bytes_val < 1024 * 1024 * 1024:
        return f"{bytes_val / (1024 * 1024):.1f} MB"
    else:
        return f"{bytes_val / (1024 * 1024 * 1024):.2f} GB"


class TestProgressTracker(tqdm):
    """Test custom tqdm class with fix for 'name' kwarg."""
    
    _callback = None
    _total_bytes = 0
    _completed_bytes = 0
    _current_file = ""
    _current_file_size = 0
    _current_file_started = False
    _lock = threading.Lock()
    
    @classmethod
    def reset_state(cls, callback, total_bytes):
        with cls._lock:
            cls._callback = callback
            cls._total_bytes = total_bytes
            cls._completed_bytes = 0
            cls._current_file = ""
            cls._current_file_size = 0
            cls._current_file_started = False
    
    @classmethod
    def set_current_file(cls, filename, size):
        with cls._lock:
            if cls._current_file and not cls._current_file_started:
                cls._completed_bytes += cls._current_file_size
            cls._current_file = filename
            cls._current_file_size = size
            cls._current_file_started = False
    
    @classmethod
    def finalize(cls):
        with cls._lock:
            if cls._current_file and not cls._current_file_started:
                cls._completed_bytes += cls._current_file_size
            cls._current_file = ""
    
    def __init__(self, *args, **kwargs):
        self._file_total = kwargs.get('total', 0) or 0
        self._file_progress = 0
        self._closed = False  # Guard against double close()
        
        with TestProgressTracker._lock:
            TestProgressTracker._current_file_started = True
        
        # Remove kwargs that tqdm doesn't recognize (HuggingFace adds 'name')
        kwargs.pop('name', None)
        super().__init__(*args, **kwargs)
    
    def update(self, n=1):
        super().update(n)
        with TestProgressTracker._lock:
            self._file_progress += n
            overall_progress = TestProgressTracker._completed_bytes + self._file_progress
            
            if TestProgressTracker._callback and TestProgressTracker._total_bytes > 0:
                percent = (overall_progress / TestProgressTracker._total_bytes) * 100
                percent = min(99.9, max(0, percent))
                TestProgressTracker._callback(percent, TestProgressTracker._current_file)
    
    def close(self):
        super().close()
        with TestProgressTracker._lock:
            # Guard against double close()
            if self._closed:
                return
            self._closed = True
            
            # Use file_progress if file_total is 0
            bytes_to_add = self._file_total if self._file_total > 0 else self._file_progress
            TestProgressTracker._completed_bytes += bytes_to_add


def progress_callback(percent, filename):
    print(f"  [{percent:5.1f}%] {filename}")


def test_download():
    print(f"tqdm version: {tqdm_module.__version__}")
    print("Testing download progress tracking...\n")
    
    repo_id = "Systran/faster-whisper-tiny"
    
    api = HfApi()
    repo_info = api.repo_info(repo_id=repo_id, repo_type="model", files_metadata=True)
    
    files_to_download = []
    total_bytes = 0
    
    for sibling in repo_info.siblings:
        file_size = sibling.size or 0
        files_to_download.append({
            'filename': sibling.rfilename,
            'size': file_size
        })
        total_bytes += file_size
    
    print(f"Total from API: {_format_bytes(total_bytes)} ({total_bytes} bytes)")
    print(f"Files: {len(files_to_download)}\n")
    
    files_to_download.sort(key=lambda x: x['size'])
    
    TestProgressTracker.reset_state(progress_callback, total_bytes)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        for file_info in files_to_download:
            filename = file_info['filename']
            file_size = file_info['size']
            display_name = filename.split('/')[-1] if '/' in filename else filename
            
            print(f"Downloading: {display_name} ({_format_bytes(file_size)})")
            TestProgressTracker.set_current_file(display_name, file_size)
            
            hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                cache_dir=tmpdir,
                local_files_only=False,
                tqdm_class=TestProgressTracker,
            )
        
        TestProgressTracker.finalize()
        
        print(f"\n{'='*50}")
        print(f"RESULTS:")
        print(f"  Expected:  {total_bytes} bytes")
        print(f"  Tracked:   {TestProgressTracker._completed_bytes} bytes")
        ratio = TestProgressTracker._completed_bytes / total_bytes
        print(f"  Ratio:     {ratio:.2f}x")
        
        if 0.95 <= ratio <= 1.05:
            print(f"\n  SUCCESS! Progress tracking is accurate.")
        else:
            print(f"\n  FAILED! Progress tracking is off by {abs(1-ratio)*100:.1f}%")


if __name__ == "__main__":
    test_download()


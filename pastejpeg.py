import sys,os,struct,subprocess
from ctypes import *
from ctypes.wintypes import *


GetClipboardFormatName = windll.user32.GetClipboardFormatNameA
EnumClipboardFormats = windll.user32.EnumClipboardFormats
CloseClipboard = windll.user32.CloseClipboard
OpenClipboard = windll.user32.OpenClipboard
GetClipboardData = windll.user32.GetClipboardData
GetClipboardData.restype = HANDLE

EmptyClipboard = windll.user32.EmptyClipboard

SetClipboardData = windll.user32.SetClipboardData
SetClipboardData.argtypes = [UINT, HANDLE]
SetClipboardData.restype = HANDLE


GlobalLock = windll.kernel32.GlobalLock
GlobalLock.argtypes=[HANDLE]
GlobalLock.restype = LPVOID

GlobalUnlock = windll.kernel32.GlobalUnlock
GlobalUnlock.argtypes=[HANDLE]
GlobalUnlock.restype = BOOL

GlobalSize = windll.kernel32.GlobalSize
GlobalSize.argtypes=[HANDLE]

GlobalAlloc = windll.kernel32.GlobalAlloc
GlobalAlloc.argtypes = [UINT, DWORD]
GlobalAlloc.restype = HGLOBAL

GMEM_MOVEABLE = 0x0002
GMEM_ZEROINIT = 0x0040
GHND          = GMEM_MOVEABLE | GMEM_ZEROINIT

CF_HDROP = 15

MessageBox = ctypes.windll.user32.MessageBoxW
MessageBox.argtypes = [HWND, LPCWSTR, LPCWSTR, UINT]
MessageBox.restype = c_int
MB_OK = 0
MB_ICONERROR = 0x00000010


PNG = 0xC154
PNGFILE='out.png'
JPEGFILE='out.jpeg'

PREDEFINED_CLIPBOARD_FORMATS={ # from winuser.h
    1:'CF_TEXT',
    2:'CF_BITMAP',
    3:'CF_METAFILEPICT',
    4:'CF_SYLK',
    5:'CF_DIF',
    6:'CF_TIFF',
    7:'CF_OEMTEXT',
    8:'CF_DIB',
    9:'CF_PALETTE',
    10:'CF_PENDATA',
    11:'CF_RIFF',
    12:'CF_WAVE',
    13:'CF_UNICODETEXT',
    14:'CF_ENHMETAFILE',
    15:'CF_HDROP',
    16:'CF_LOCALE',
    17:'CF_DIBV5',
}

CLI_MODE = '--gui' not in sys.argv

def throw_error(message):
	if CLI_MODE:
		print(message)
	else:
		MessageBox(None, message, "pastejpeg.py", MB_OK | MB_ICONERROR)

def get_clipboard_format_name(format):
	if format in PREDEFINED_CLIPBOARD_FORMATS:
		return PREDEFINED_CLIPBOARD_FORMATS[format]
	buffer=bytes(" "*256,"ascii")
	ret = GetClipboardFormatName(format, buffer, len(buffer))
	if ret == 0:
		return "UNKNOWN_FORMAT"
	else:
		return buffer.decode('ascii').split('\0')[0]

def get_binary_object_from_clipboard(format):
	handle = GetClipboardData(format)
	if handle is None:
		throw_error("Failed to get format {:04x}".format(format))
		return None
	data = GlobalLock(handle)
	if data==0:
		throw_error("Failed to lock global data. Handle is {}".format(handle))
		return None
	try:
		size = GlobalSize(handle)
		print("size={}".format(size))
		buffer = string_at(data, size)
		return buffer
	finally:
		GlobalUnlock(handle)

def build_dropfiles(files):
	names='\0'.join(list(files)+['','']).encode('utf-16-le')
	main_struct_format = '<lllll'
	file_list_format = '{}s'.format(len(names))
	
	return struct.pack(main_struct_format + file_list_format,
		struct.calcsize(main_struct_format), # pFiles (offset to start of strings)
		0,                                   # PT.x (drop position)
		0,                                   # PT.y (drop position)
		0,                                   # fNC (FALSE)
		1,                                   # fWide (TRUE)
		names                                # The file list following the main struct
	)

def copy_file_to_clipboard(path):
	fullpath = os.path.abspath(path)
	buffer = build_dropfiles([fullpath])
	handle = GlobalAlloc(GHND, len(buffer))
	if handle is None:
		throw_error("Failed to allocate global memory!")
		return None
	mem_pointer = GlobalLock(handle)
	if mem_pointer == 0:
		throw_error("Failed to lock global memory!")
		return None 
	buffer_ptr = create_string_buffer(buffer)
	memmove(mem_pointer, buffer_ptr,len(buffer))
	GlobalUnlock(handle)
	ret = EmptyClipboard()
	if ret == 0:
		throw_error("Failed to empty clipboard!")
		return None

	ret_handle = SetClipboardData(CF_HDROP,handle)
	if ret_handle is None:
		throw_error("Failed to set the clipboard data!")
		return None
	return True



def get_clipboard_formats():
	out={}
	ret = 0
	while True:
		ret = EnumClipboardFormats(ret)
		if ret==0:
			return out
		name = get_clipboard_format_name(ret)
		out[ret]=name

ret=OpenClipboard(0)
if ret==0:
	throw_error("Failed to open clipboard")
	sys.exit(1)
try:
	formats = get_clipboard_formats()
	for format, name in formats.items():
		print("Clipboard format: {:04x}: {}".format(format,name))

	if PNG in formats:
		buffer = get_binary_object_from_clipboard(PNG)
		if buffer is not None:
			# TODO: skip creating the file and just pipe it into imagemagick
			with open('out.png','wb') as f:
				f.write(buffer)
			pngsize = len(buffer)
			subprocess.check_call(['magick','convert',PNGFILE,JPEGFILE])
			try:
				os.unlink(PNGFILE)
			except OSError:
				pass # we don't care if we failed to delete it. We just want to clean up
				# we don't delete the jpeg because it has to continue existing for the copy of the file-path to work

			if pngsize < os.path.getsize(JPEGFILE):
				pass # Do nothing, the PNG is smaller anyway.
				print("PNG is smaller than the JPEG! keeping the PNG there.")
			else:
				copy_file_to_clipboard(JPEGFILE)
				print("Converted to a JPEG and copied the path")
	else:
		# print rather than throwing an error, because in GUI mode we don't want to pop up an error box for this
		print("PNG not in formats! skipping.")

finally:
	ret=CloseClipboard()
	if ret==0:
		throw_error("Failed to close clipboard!")
		sys.exit(2)

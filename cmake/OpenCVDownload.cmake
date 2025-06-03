#
#  Download and optionally unpack a file
#
#  ocv_download(FILENAME p HASH h URL u1 [u2 ...] DESTINATION_DIR d [ID id] [STATUS s] [UNPACK] [RELATIVE_URL])
#    FILENAME - filename
#    HASH - MD5 hash
#    URL - full download url (first nonempty value will be chosen)
#    DESTINATION_DIR - file will be copied to this directory
#    ID     - identifier for project/group of downloaded files
#    STATUS - passed variable will be updated in parent scope,
#             function will not fail the build in case of download problem if this option is provided,
#             but will fail in case when other operations (copy, remove, etc.) failed
#    UNPACK - downloaded file will be unpacked to DESTINATION_DIR
#    RELATIVE_URL - if set, then URL is treated as a base, and FILENAME will be appended to it
#  Note: uses OPENCV_DOWNLOAD_PATH folder as cache, default is <opencv>/.cache

set(HELP_OPENCV_DOWNLOAD_PATH "Cache directory for downloaded files")
if(DEFINED ENV{OPENCV_DOWNLOAD_PATH})
  set(OPENCV_DOWNLOAD_PATH "$ENV{OPENCV_DOWNLOAD_PATH}" CACHE PATH "${HELP_OPENCV_DOWNLOAD_PATH}")
endif()
set(OPENCV_DOWNLOAD_PATH "${OpenCV_SOURCE_DIR}/.cache" CACHE PATH "${HELP_OPENCV_DOWNLOAD_PATH}")
set(OPENCV_DOWNLOAD_LOG "${OpenCV_BINARY_DIR}/CMakeDownloadLog.txt")
set(OPENCV_DOWNLOAD_WITH_CURL "${OpenCV_BINARY_DIR}/download_with_curl.sh")
set(OPENCV_DOWNLOAD_WITH_WGET "${OpenCV_BINARY_DIR}/download_with_wget.sh")
set(OPENCV_DOWNLOAD_TRIES_LIST 1 CACHE STRING "List of download tries") # a list
set(OPENCV_DOWNLOAD_PARAMS INACTIVITY_TIMEOUT 60 TIMEOUT 600 CACHE STRING "Download parameters to be passed to file(DOWNLOAD ...)")
mark_as_advanced(OPENCV_DOWNLOAD_TRIES_LIST OPENCV_DOWNLOAD_PARAMS)

# Init download cache directory and log file and helper scripts
if(NOT EXISTS "${OPENCV_DOWNLOAD_PATH}")
  file(MAKE_DIRECTORY ${OPENCV_DOWNLOAD_PATH})
endif()
if(NOT EXISTS "${OPENCV_DOWNLOAD_PATH}/.gitignore")
  file(WRITE "${OPENCV_DOWNLOAD_PATH}/.gitignore" "*\n")
endif()
file(WRITE "${OPENCV_DOWNLOAD_LOG}" "#use_cache \"${OPENCV_DOWNLOAD_PATH}\"\n")
file(REMOVE "${OPENCV_DOWNLOAD_WITH_CURL}")
file(REMOVE "${OPENCV_DOWNLOAD_WITH_WGET}")

ocv_check_environment_variables(OPENCV_DOWNLOAD_MIRROR_ID)

function(ocv_init_download_mirror)
  message(STATUS "ocv_init_download: No downloading as per Debian policy.")
endfunction()

function(ocv_download)
  message(STATUS "ocv_download: Not downloading ${FILENAME} from ${URL} as per Debian policy.")
endfunction()

# ----------------------------------------------------------------------------
#  Initialize download in case mirror is used
# ----------------------------------------------------------------------------
ocv_init_download_mirror()

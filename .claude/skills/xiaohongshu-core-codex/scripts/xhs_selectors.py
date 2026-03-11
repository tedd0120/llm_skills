"""
小红书 DOM 选择器集中管理（codex）
共享给抓取与认证逻辑使用。
"""


class XHSSelectors:
    # 登录相关
    LOGIN_MODAL = ".login-container"
    LOGIN_OVERLAY = ".login-vdiceas"
    LOGIN_MODAL_TITLE = ".login-container .title"
    QR_CODE_IMAGE = ".qrcode-img"
    LOGIN_SUCCESS_ELEMENT = ".user .name"
    LOGIN_BUTTON_TEXT = "登录"

    # 搜索相关
    SEARCH_INPUT = "input.search-input"
    SEARCH_BUTTON = ".search-icon"

    # 搜索结果页
    FEEDS_CONTAINER = ".feeds-container"
    POST_CARD = "section.note-item"
    POST_LINK = "a.cover.mask.ld"
    POST_LINK_EXPLORE = "a[href*='/explore/']"

    # 帖子详情页
    POST_DETAIL_CONTAINER = "#noteContainer"
    POST_TITLE = "#detail-title"
    POST_CONTENT = "#detail-desc .note-text"
    POST_AUTHOR = ".author-container .username"
    POST_DATE = ".date"
    POST_BOTTOM_AUTHOR = ".author-wrapper"

    # 互动数据
    LIKE_COUNT = ".like-wrapper .count"
    COLLECT_COUNT = ".collect-wrapper .count"
    COMMENT_COUNT = ".chat-wrapper .count"
    SHARE_COUNT = ".share-wrapper .count"

    # 评论区
    COMMENT_CONTAINER = "#noteContainer .comments-container"
    COMMENT_ITEM = ".comment-item"
    COMMENT_CONTENT = ".comment-item .content"
    COMMENT_AUTHOR = ".comment-item .author .name"
    MORE_COMMENTS_BUTTON = "text=展开更多评论"
    SHOW_MORE_REPLY = "text=展开"

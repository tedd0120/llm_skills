"""
小红书 DOM 选择器集中管理
为了应对小红书可能的改版，将所有关键的 CSS/XPath 选择器集中于此

最后验证时间: 2026-08-15  (基于实际页面 DOM 分析)
"""

class XHSSelectors:
    # --- 登录相关 ---
    LOGIN_MODAL = ".login-container"
    LOGIN_OVERLAY = ".login-vdiceas"  # 登录弹窗遮罩层
    LOGIN_MODAL_TITLE = ".login-container .title"  # 登录弹窗标题
    QR_CODE_IMAGE = ".qrcode-img"  # 注意：页面上的二维码不一定意味着未登录
    LOGIN_SUCCESS_ELEMENT = ".user .name"  # 登录成功后会出现用户名
    LOGIN_BUTTON_TEXT = "登录"
    
    # --- 搜索相关 ---
    SEARCH_INPUT = "input.search-input"
    SEARCH_BUTTON = ".search-icon"
    
    # --- 搜索结果页 ---
    FEEDS_CONTAINER = ".feeds-container"
    POST_CARD = "section.note-item"
    
    # 帖子链接: 有两种形式
    # 1. a[href*='/explore/'] - 无 class, 直接链接帖子
    # 2. a.cover.mask.ld[href*='/search_result/'] - 带 token 的链接
    # 我们使用 /search_result/ 的链接，因为它带有 xsec_token 可以正常访问
    POST_LINK = "a.cover.mask.ld"
    POST_LINK_EXPLORE = "a[href*='/explore/']"
    
    # --- 帖子详情页 ---
    POST_DETAIL_CONTAINER = "#noteContainer"
    POST_TITLE = "#noteContainer #detail-title"
    POST_CONTENT = "#noteContainer #detail-desc .note-text, #noteContainer .note-content, #noteContainer #detail-desc"
    POST_AUTHOR = "#noteContainer .author-container .username"
    POST_DATE = "#noteContainer .bottom-container .date, #noteContainer .date"
    POST_BOTTOM_AUTHOR = "#noteContainer .author-wrapper"
    POST_DETAIL_LINK = "#noteContainer a[href*='/explore/'], #noteContainer a[href*='/discovery/item/']"
    
    # 互动数据
    LIKE_COUNT = "#noteContainer .like-wrapper .count"
    COLLECT_COUNT = "#noteContainer .collect-wrapper .count"
    COMMENT_COUNT = "#noteContainer .chat-wrapper .count"
    SHARE_COUNT = "#noteContainer .share-wrapper .count"
    
    # 关闭按钮
    CLOSE_BUTTON = ".close-circle"
    
    # --- 评论区 ---
    COMMENT_CONTAINER = "#noteContainer .comments-container"
    COMMENT_ITEM = ".comment-item"
    COMMENT_CONTENT = ".comment-item .content"
    COMMENT_AUTHOR = ".comment-item .author .name"
    COMMENT_LIKE_COUNT = ".like-wrapper .count"
    
    # 展开更多评论
    MORE_COMMENTS_BUTTON = "text=展开更多评论"
    SHOW_MORE_REPLY = "text=展开"

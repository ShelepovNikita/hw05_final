
CREATE_POST_TEMPLATE = 'posts/create_post.html'
INDEX_TEMPLATE = 'posts/index.html'
FOLLOW_PAGE_TEMPLATE = 'posts/follow.html'
GROUP_LIST_TEMPLATE = 'posts/group_list.html'
PROFILE_TEMPLATE = 'posts/profile.html'
POST_DETAIL_TEMPLATE = 'posts/post_detail.html'
UNEXISTING_PAGE_TEMPLATE = 'core/404.html'


CREATE_POST_URL = 'posts:post_create'
INDEX_URL = 'posts:index'
FOLLOW_PAGE_URL = 'posts:follow_index'
GROUP_LIST_URL = 'posts:group_list'
PROFILE_URL = 'posts:profile'
POST_DETAIL_URL = 'posts:post_detail'
UNEXISTING_PAGE_URL = '/unexisting_page/'
UPDATE_POST_URL = 'posts:update_post'

ADD_COMMENT_URL = 'posts:add_comment'
PROFILE_FOLLOW_URL = 'posts:profile_follow'
PROFILE_UNFOLLOW_URL = 'posts:profile_unfollow'

TEST_IMAGE = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)
NAME_OF_IMAGE = 'test.gif'
IMAGE = f'posts/{NAME_OF_IMAGE}'

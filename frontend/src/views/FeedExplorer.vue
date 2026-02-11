<template>
  <div>
    <!-- Header -->
    <div class="mb-4 md:mb-6">
      <div class="flex items-center justify-between flex-wrap gap-4">
        <div class="flex items-center gap-2">
          <RssIcon class="w-6 h-6 md:w-7 md:h-7 text-gray-900" aria-hidden="true" />
          <h1 class="text-xl md:text-2xl lg:text-3xl font-semibold text-gray-900">Feed Explorer</h1>
        </div>
        <div class="flex items-center gap-3">
          <!-- Account Selector -->
          <div class="flex items-center gap-2">
            <label class="text-sm font-medium text-gray-700 whitespace-nowrap">Account:</label>
            <select
              v-model="accountId"
              @change="handleAccountChange"
              :disabled="loading || switchingAccount || availableAccounts.length === 0"
              class="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white min-w-[140px] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <option value="" disabled>
                {{ availableAccounts.length === 0 ? 'No accounts available' : 'Select Account' }}
              </option>
              <option
                v-for="account in availableAccounts"
                :key="account.account_id || account"
                :value="account.account_id || account"
              >
                {{ account.account_id || account }}
              </option>
            </select>
            <div v-if="switchingAccount" class="flex items-center gap-2 text-sm text-gray-500">
              <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-500"></div>
              <span>Switching...</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Account Info Card -->
    <Card v-if="accountId" class="mb-6">
      <div class="space-y-4">
        <div class="flex items-center justify-between flex-wrap gap-4">
          <div class="flex items-center gap-4">
            <div class="flex items-center gap-2">
              <div class="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center">
                <span class="text-primary-600 font-semibold text-sm">
                  {{ accountId.charAt(accountId.length - 1) }}
                </span>
              </div>
              <div>
                <div class="font-semibold text-gray-900">{{ accountId }}</div>
                <div class="text-xs text-gray-500">Active Account</div>
              </div>
            </div>
            <div class="flex items-center gap-4 text-sm">
              <div class="flex items-center gap-2">
                <div class="w-2 h-2 rounded-full" :class="sessionStatus === 'active' ? 'bg-green-500' : sessionStatus === 'loading' ? 'bg-yellow-500' : 'bg-gray-400'"></div>
                <span class="text-gray-600">Session: <span class="font-medium">{{ sessionStatusText }}</span></span>
              </div>
              <div v-if="stats?.cache" class="flex items-center gap-2">
                <span class="text-gray-600">Cache:</span>
                <span class="font-medium" :class="stats.cache.enabled ? 'text-green-600' : 'text-gray-400'">
                  {{ stats.cache.enabled ? 'Active' : 'Disabled' }}
                </span>
              </div>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <Button
              @click="handleLoadStats"
              :disabled="loadingStats || !accountId"
              :loading="loadingStats"
              variant="outline"
              size="sm"
              title="Check session status (opens browser)"
            >
              <ArrowPathIcon class="w-4 h-4 mr-1" />
              Check Session
            </Button>
          </div>
        </div>
        
        <!-- Advanced Settings (Collapsible) -->
        <div class="border-t border-gray-200 pt-4">
          <button
            @click="showAdvancedSettings = !showAdvancedSettings"
            class="flex items-center justify-between w-full text-left text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors"
          >
            <div class="flex items-center gap-2">
              <span>Advanced Settings</span>
              <InformationCircleIcon class="w-4 h-4 text-gray-400" title="Browser profile path configuration" />
            </div>
            <ChevronDownIcon v-if="!showAdvancedSettings" class="w-5 h-5 text-gray-400" />
            <ChevronUpIcon v-else class="w-5 h-5 text-gray-400" />
          </button>
          
          <div v-if="showAdvancedSettings" class="mt-4 space-y-4">
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <div class="flex items-start gap-2">
                <InformationCircleIcon class="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <div class="text-sm text-blue-800">
                  <p class="font-medium mb-1">Browser Profile Path (Client-Side Profile)</p>
                  <p class="text-xs">
                    Specify a browser profile path to use a persistent browser context. 
                    If not specified, a temporary browser context will be used (more secure).
                    Profile path is loaded from account metadata but can be overridden here.
                  </p>
                </div>
              </div>
            </div>
            
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Profile Path (Optional)
                </label>
                <div class="space-y-2">
                  <input
                    v-model="profilePathOverride"
                    type="text"
                    class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="/home/user/browser_profiles/my_profile"
                  />
                  <div v-if="currentProfilePath" class="text-xs text-gray-500">
                    <span class="font-medium">From account metadata:</span> {{ currentProfilePath }}
                  </div>
                  <div v-else class="text-xs text-gray-500">
                    No profile path in account metadata. Using temporary browser context.
                  </div>
                </div>
              </div>
              
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Profile Directory (Alias for Profile Path)
                </label>
                <input
                  v-model="profileDirOverride"
                  type="text"
                  class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="/home/user/browser_profiles/my_profile"
                />
              </div>
              
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                    Profile ID
                  </label>
                  <input
                    v-model="profileIdOverride"
                    type="text"
                    class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="account_01"
                  />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                    Base Directory
                  </label>
                  <input
                    v-model="baseDirectoryOverride"
                    type="text"
                    class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="/home/user/profiles"
                  />
                </div>
              </div>
            </div>

            <!-- Clear Cache (Dangerous Action) -->
            <div class="border-t border-gray-200 pt-4">
              <div class="bg-red-50 border border-red-200 rounded-lg p-3 mb-3">
                <div class="flex items-start gap-2">
                  <svg class="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <div class="text-sm text-red-800">
                    <p class="font-medium mb-1">Clear Cache</p>
                    <p class="text-xs">
                      This will clear all cached feed data for the current account and automatically refresh the feed. This action cannot be undone.
                    </p>
                  </div>
                </div>
              </div>
              <Button 
                @click="handleClearCache" 
                :disabled="loadingFeed || !accountId"
                class="w-full bg-red-600 hover:bg-red-700 text-white border-red-600 hover:border-red-700"
                size="sm"
                title="Clear cache and automatically refresh feed"
              >
                <svg class="w-4 h-4 mr-1 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Clear Cache
              </Button>
            </div>
          </div>
        </div>
      </div>
    </Card>

    <Alert
      v-if="error"
      type="error"
      :message="error"
      dismissible
      @dismiss="error = null"
    />

    <Alert
      v-if="availableAccounts.length === 0 && isMounted"
      type="warning"
      message="No accounts found. Please create an account first."
      dismissible
      @dismiss="() => {}"
    />

    <Alert
      v-else-if="!accountId && isMounted"
      type="warning"
      message="Please select an account to start using Feed Explorer"
      dismissible
      @dismiss="() => {}"
    />

    <!-- Tabs -->
    <div class="mb-6">
      <div class="border-b border-gray-200">
        <nav class="-mb-px flex space-x-8">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="handleTabClick(tab.id)"
            :class="[
              'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors',
              activeTab === tab.id
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            ]"
          >
            {{ tab.label }}
          </button>
        </nav>
      </div>
    </div>

    <!-- Tab: Feed -->
    <div v-if="activeTab === 'feed'" class="space-y-6">
      <!-- Cache Indicator -->
      <Card v-if="feedItems.length > 0" class="bg-blue-50 border-blue-200">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="text-sm text-blue-700">
              📦 Showing {{ feedItems.length }} cached feed items
            </span>
            <span v-if="feedItems[0]?.fetched_at" class="text-xs text-blue-600">
              (Last updated: {{ formatTimeAgo(feedItems[0].fetched_at) }})
            </span>
          </div>
          <span class="text-xs text-blue-600 bg-blue-100 px-2 py-1 rounded">
            Cached Data
          </span>
        </div>
      </Card>
      
      <!-- Filters & Controls -->
      <Card>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Time Range</label>
            <select
              v-model="timeRange"
              class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="30">30 days</option>
              <option value="7">7 days</option>
              <option value="1">Today</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Min Likes</label>
            <input
              v-model.number="filters.min_likes"
              type="number"
              class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              placeholder="100"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Has Media</label>
            <select
              v-model="filters.has_media"
              class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option :value="null">All</option>
              <option :value="true">Yes</option>
              <option :value="false">No</option>
            </select>
          </div>
          <div class="flex items-end">
            <div class="w-full">
              <Button 
                @click="handleLoadFeed" 
                :disabled="loadingFeed || !accountId" 
                :loading="loadingFeed" 
                variant="primary"
                class="w-full"
                :title="!accountId ? 'Please select an account first' : 'Fetch new feed data from Threads'"
              >
                <ArrowPathIcon class="w-4 h-4 mr-1" />
                Refresh Feed
              </Button>
              <p v-if="loadingFeed" class="text-xs text-gray-500 mt-1 text-center">
                Refreshing feed...
              </p>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Username</label>
            <input
              v-model="filters.username"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              placeholder="@username"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Text Contains</label>
            <input
              v-model="filters.text_contains"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              placeholder="Search text..."
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Min Replies</label>
            <input
              v-model.number="filters.min_replies"
              type="number"
              class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              placeholder="5"
            />
          </div>
        </div>
      </Card>

      <!-- Stats & Quick Actions -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Feed Stats -->
        <Card>
          <div class="space-y-3">
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-sm font-semibold text-gray-900">📊 Feed Stats</h3>
              <span v-if="accountId" class="text-xs px-2 py-1 bg-primary-100 text-primary-700 rounded">
                {{ accountId }}
              </span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-sm text-gray-600">Total Items:</span>
              <span class="text-lg font-semibold">{{ feedStats.total || 0 }}</span>
            </div>
            <div v-if="hasActiveFilters" class="flex justify-between items-center">
              <span class="text-sm text-gray-600">Matched/After Filter:</span>
              <span class="text-lg font-semibold">{{ feedStats.filtered || 0 }}</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-sm text-gray-600">Showing:</span>
              <span class="text-lg font-semibold">{{ feedStats.showing || feedItems.length }}</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-sm text-gray-600">Cache Status:</span>
              <span class="text-sm font-semibold" :class="stats?.cache?.enabled ? 'text-green-600' : 'text-gray-400'">
                {{ stats?.cache?.enabled ? '✓ Active' : '✗ Disabled' }}
              </span>
            </div>
            <div v-if="stats?.cache?.lastUpdated" class="flex justify-between items-center">
              <span class="text-sm text-gray-600">Last Updated:</span>
              <span class="text-sm font-medium">{{ formatTimeAgo(stats.cache.lastUpdated) }}</span>
            </div>
            <div v-if="stats?.cache?.ageFormatted" class="flex justify-between items-center">
              <span class="text-sm text-gray-600">Cache Age:</span>
              <span class="text-sm font-medium">{{ stats.cache.ageFormatted }}</span>
            </div>
          </div>
        </Card>

        <!-- Quick Actions -->
        <Card class="lg:col-span-2">
          <div class="space-y-3">
            <h3 class="text-sm font-semibold text-gray-900 mb-3">⚡ Quick Actions</h3>
            <div class="grid grid-cols-3 gap-3">
              <Button @click="activeTab = 'user-posts'" variant="outline" size="sm" class="w-full">
                👤 User Posts
              </Button>
              <Button @click="activeTab = 'browse'" variant="outline" size="sm" class="w-full">
                💬 Browse & Comment
              </Button>
              <Button 
                @click="showFeedInsights = true" 
                :disabled="feedItems.length === 0"
                variant="outline" 
                size="sm" 
                class="w-full"
                title="View feed analytics and insights"
              >
                📊 Feed Insights
              </Button>
            </div>
          </div>
        </Card>
      </div>

      <!-- Feed Items - Premium Table -->
      <Card class="shadow-lg">
        <template #header>
          <div class="flex items-center justify-between flex-wrap gap-4">
            <div>
              <div class="flex items-center gap-3">
                <div class="p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg">
                  <RssIcon class="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 class="text-lg font-bold text-gray-900">Feed Items</h3>
                  <p class="text-sm text-gray-600 mt-0.5">
                    <span class="font-semibold text-gray-900">{{ feedItems.length }}</span> items
                    <span v-if="totalItems > feedItems.length" class="text-gray-500">
                      of <span class="font-medium">{{ totalItems }}</span> total
                    </span>
                    <span v-if="feedItems[0]?.fetched_at" class="text-gray-400">
                      • Updated {{ formatTimeAgo(feedItems[0].fetched_at) }}
                    </span>
                  </p>
                </div>
                <span v-if="accountId" class="px-3 py-1 bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 text-blue-700 rounded-full text-xs font-semibold">
                  {{ accountId }}
                </span>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <select class="px-3 py-2 border border-gray-300 rounded-lg text-sm font-medium bg-white hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors">
                <option>Sort: Latest</option>
                <option>Sort: Most Likes</option>
                <option>Sort: Most Replies</option>
              </select>
              <Button variant="outline" size="sm" class="font-medium">Export</Button>
            </div>
          </div>
        </template>
        
        <!-- Feed Items - Card Grid Layout -->
        <div class="space-y-3 p-4">
          <!-- Empty States -->
          <div v-if="!accountId && !loading" class="py-16 text-center">
            <div class="flex flex-col items-center gap-3">
              <div class="w-16 h-16 rounded-full bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center">
                <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <div class="text-gray-600 font-semibold text-lg">Please select an account</div>
              <div class="text-sm text-gray-500 max-w-md">Choose an account from the dropdown above to start exploring feeds</div>
            </div>
          </div>
          <div v-else-if="feedItems.length === 0 && !loading" class="py-16 text-center">
            <div class="flex flex-col items-center gap-3">
              <div class="w-16 h-16 rounded-full bg-gradient-to-br from-blue-100 to-purple-100 flex items-center justify-center">
                <svg class="w-8 h-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                </svg>
              </div>
              <div class="text-gray-600 font-semibold text-lg">No cached feed items found</div>
              <div class="text-sm text-gray-500">Click <span class="font-semibold text-blue-600">"Refresh Feed"</span> to fetch new data for <span class="font-semibold text-primary-600">{{ accountId }}</span></div>
              <div class="text-xs text-gray-400 mt-1 px-3 py-1 bg-gray-50 rounded-full">Data will be automatically saved to database</div>
            </div>
          </div>
          
          <!-- Feed Items -->
          <FeedItem
            v-for="(item, index) in feedItems"
            :key="item.post_id"
            :item="item"
            :index="index"
            :get-avatar-url="getAvatarUrl"
            :get-media-url="getMediaUrl"
            :format-time-ago="formatTimeAgo"
            :format-number="formatNumber"
            @view-media="handleViewMedia"
            @like="handleLikePost"
            @comment="handleCommentPost"
            @repost="handleRepostPost"
          />
        </div>
        
        <!-- Pagination -->
        <div v-if="totalItems > 0" class="mt-6 px-4">
          <Pagination
            :current-page="currentPage"
            :page-size="pageSize"
            :total="totalItems"
            :page-size-options="[10, 20, 50, 100]"
            :loading="loading"
            @page-change="handlePageChange"
            @page-size-change="handlePageSizeChange"
          />
        </div>
      </Card>

      <!-- Media Gallery Modal -->
    </div>

    <!-- Tab: User Posts -->
    <div v-else-if="activeTab === 'user-posts'" class="space-y-6">
      <!-- User Selection -->
      <Card>
        <div class="flex flex-col md:flex-row gap-4">
          <div class="flex-1">
            <label class="block text-sm font-medium text-gray-700 mb-1">Username</label>
            <div class="flex gap-2">
              <input
                v-model="selectedUsername"
                type="text"
                class="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm"
                placeholder="@may__lily"
              />
              <Button @click="handleLoadUserPosts" :disabled="loading || !selectedUsername" :loading="loading">
                🔍 Search
              </Button>
              <Button @click="handleLoadUserPosts" :disabled="loading || !selectedUsername" :loading="loading" variant="primary">
                📥 Load Posts
              </Button>
            </div>
          </div>
        </div>
      </Card>

      <!-- User Profile & Stats -->
      <div v-if="selectedUser" class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <h3 class="text-sm font-semibold text-gray-900 mb-3">👤 User Profile</h3>
          <div class="space-y-2">
            <div class="flex items-center gap-2">
              <span class="font-medium">@{{ selectedUser.username }}</span>
              <span v-if="selectedUser.is_verified" class="text-blue-500">✓</span>
            </div>
            <div v-if="selectedUser.user_display_name" class="text-sm text-gray-600">
              {{ selectedUser.user_display_name }}
            </div>
          </div>
        </Card>
        <Card>
          <h3 class="text-sm font-semibold text-gray-900 mb-3">📊 User Stats</h3>
          <div class="space-y-2 text-sm">
            <div class="flex justify-between">
              <span class="text-gray-600">Total Posts:</span>
              <span class="font-semibold">{{ userPosts.length }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">Avg Likes:</span>
              <span class="font-semibold">{{ averageLikes }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">Avg Replies:</span>
              <span class="font-semibold">{{ averageReplies }}</span>
            </div>
            <div class="flex gap-2 mt-3">
              <Button @click="handleFollowUser(selectedUser.username)" size="sm" variant="primary">
                Follow
              </Button>
              <Button @click="handleUnfollowUser(selectedUser.username)" size="sm" variant="outline">
                Unfollow
              </Button>
            </div>
          </div>
        </Card>
      </div>

      <!-- Comment User Posts -->
      <Card v-if="selectedUsername">
        <h3 class="text-sm font-semibold text-gray-900 mb-4">💬 Comment User Posts</h3>
        <div class="space-y-4">
          <!-- Filter Criteria -->
          <div class="border border-gray-200 rounded-lg p-4">
            <h4 class="text-sm font-medium text-gray-700 mb-3">Filter Criteria:</h4>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-xs text-gray-600 mb-1">Min Likes</label>
                <input v-model.number="userCommentPostsConfig.filter_criteria.min_likes" type="number" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm" />
              </div>
              <div>
                <label class="block text-xs text-gray-600 mb-1">Max Likes</label>
                <input v-model.number="userCommentPostsConfig.filter_criteria.max_likes" type="number" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm" />
              </div>
              <div>
                <label class="block text-xs text-gray-600 mb-1">Has Media</label>
                <select v-model="userCommentPostsConfig.filter_criteria.has_media" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm">
                  <option :value="null">All</option>
                  <option :value="true">Yes</option>
                  <option :value="false">No</option>
                </select>
              </div>
              <div>
                <label class="block text-xs text-gray-600 mb-1">Min Replies</label>
                <input v-model.number="userCommentPostsConfig.filter_criteria.min_replies" type="number" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm" />
              </div>
            </div>
          </div>

          <!-- Comment Settings -->
          <div class="border border-gray-200 rounded-lg p-4">
            <h4 class="text-sm font-medium text-gray-700 mb-3">Comment Settings:</h4>
            <div class="space-y-3">
              <div>
                <label class="block text-xs text-gray-600 mb-1">Max Posts to Comment</label>
                <input v-model.number="userCommentPostsConfig.max_posts_to_comment" type="number" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm" min="1" max="100" />
              </div>
              <div>
                <label class="flex items-center gap-2">
                  <input v-model="userCommentPostsConfig.random_selection" type="checkbox" class="rounded" />
                  <span class="text-xs text-gray-600">Random Selection</span>
                </label>
              </div>
              <div>
                <label class="block text-xs text-gray-600 mb-1">Comment Delay (ms)</label>
                <div class="flex gap-2">
                  <input v-model.number="userCommentPostsConfig.comment_delay_min" type="number" placeholder="Min" class="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm" min="1000" />
                  <input v-model.number="userCommentPostsConfig.comment_delay_max" type="number" placeholder="Max" class="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm" min="1000" />
                </div>
                <p v-if="userCommentPostsConfig.comment_delay_max < userCommentPostsConfig.comment_delay_min" class="text-xs text-red-600 mt-1">
                  Max delay must be >= Min delay
                </p>
              </div>
              <div>
                <label class="block text-xs text-gray-600 mb-1">Max Items to Extract</label>
                <input v-model.number="userCommentPostsConfig.max_items" type="number" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm" min="1" max="500" />
              </div>
              <div>
                <label class="block text-xs text-gray-600 mb-1">Comment Templates</label>
                <div class="flex flex-wrap gap-2">
                  <button
                    v-for="(template, idx) in userCommentPostsConfig.comment_templates"
                    :key="idx"
                    @click="userCommentPostsConfig.comment_templates.splice(idx, 1)"
                    class="px-2 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50"
                  >
                    {{ template }} ×
                  </button>
                  <button
                    @click="addUserCommentPostsTemplate"
                    class="px-2 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50 text-blue-600"
                  >
                    + Add Template
                  </button>
                </div>
              </div>
            </div>
          </div>

          <Button @click="handleCommentUserPosts" :disabled="loading || !selectedUsername" :loading="loading" variant="primary" size="lg" class="w-full">
            🚀 Start Commenting on User Posts
          </Button>
        </div>

        <!-- Progress & Results -->
        <div v-if="userCommentPostsResults" class="mt-6 border-t border-gray-200 pt-4">
          <h4 class="text-sm font-semibold text-gray-900 mb-3">📊 Progress & Results</h4>
          <div class="space-y-3">
            <div>
              <div class="flex justify-between text-sm mb-1">
                <span>Status:</span>
                <span class="font-medium">{{ userCommentPostsResults.status || 'In Progress' }}</span>
              </div>
              <div class="w-full bg-gray-200 rounded-full h-2">
                <div
                  class="bg-primary-500 h-2 rounded-full transition-all"
                  :style="{ width: `${userCommentPostsProgress}%` }"
                ></div>
              </div>
              <div class="text-xs text-gray-600 mt-1">
                {{ userCommentPostsResults.totalCommented || 0 }} / {{ userCommentPostsConfig.max_posts_to_comment }} posts commented
              </div>
            </div>
            <div v-if="userCommentPostsResults.results && userCommentPostsResults.results.length > 0" class="space-y-2">
              <div class="text-sm font-medium">Results:</div>
              <div
                v-for="(result, idx) in userCommentPostsResults.results"
                :key="idx"
                class="p-2 rounded border text-sm"
                :class="result.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'"
              >
                <span :class="result.success ? 'text-green-600' : 'text-red-600'">
                  {{ result.success ? '✅' : '❌' }} @{{ result.username }} - {{ result.success ? 'Commented' : 'Failed' }}: "{{ result.comment }}"
                </span>
              </div>
            </div>
          </div>
        </div>
      </Card>

      <!-- User Posts Table -->
      <Card v-if="userPosts.length > 0">
        <template #header>
          <h3 class="text-lg font-semibold text-gray-900">📋 User Posts ({{ userPosts.length }} items)</h3>
        </template>
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Post ID</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Text Preview</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Likes</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Replies</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="item in userPosts" :key="item.post_id" class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ item.shortcode || item.post_id }}</td>
                <td class="px-6 py-4">
                  <div class="text-sm text-gray-900 max-w-md truncate">{{ item.text || 'No text' }}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">{{ formatNumber(item.like_count) }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">{{ formatNumber(item.reply_count) }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">
                  <div class="flex gap-2">
                    <button @click="handleLikePost(item.post_id)" class="text-red-500 hover:text-red-700">❤️</button>
                    <button @click="handleCommentPost(item)" class="text-blue-500 hover:text-blue-700">💬</button>
                    <button @click="handleRepostPost(item.post_id)" class="text-green-500 hover:text-green-700">↻</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>
    </div>

    <!-- Tab: Interactions -->
    <div v-else-if="activeTab === 'interactions'" class="space-y-6">
      <!-- Post Interaction -->
      <Card>
        <h3 class="text-sm font-semibold text-gray-900 mb-3">🎯 Post Interaction</h3>
        <div class="flex gap-2">
          <input
            v-model="interactionPostId"
            type="text"
            class="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm"
            placeholder="Post ID or URL (e.g., DT8F9qykxdc)"
          />
          <Button @click="handleLoadPost" :disabled="loading || !interactionPostId" :loading="loading">
            🔍 Load
          </Button>
        </div>
      </Card>

      <!-- Post Info & Actions -->
      <div v-if="selectedPost" class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <h3 class="text-sm font-semibold text-gray-900 mb-3">📊 Post Info</h3>
          <div class="space-y-2 text-sm">
            <div><span class="text-gray-600">Post ID:</span> <span class="font-medium">{{ selectedPost.post_id }}</span></div>
            <div><span class="text-gray-600">Username:</span> <span class="font-medium">@{{ selectedPost.username }}</span></div>
            <div><span class="text-gray-600">Likes:</span> <span class="font-medium">{{ formatNumber(selectedPost.like_count) }}</span></div>
            <div><span class="text-gray-600">Replies:</span> <span class="font-medium">{{ formatNumber(selectedPost.reply_count) }}</span></div>
            <div><span class="text-gray-600">Status:</span> <span class="font-medium text-green-600">Liked ✓</span></div>
          </div>
        </Card>
        <Card>
          <h3 class="text-sm font-semibold text-gray-900 mb-3">⚡ Quick Actions</h3>
          <div class="grid grid-cols-2 gap-2">
            <Button @click="handleLikePost(selectedPost.post_id)" size="sm" variant="primary">❤️ Like</Button>
            <Button @click="handleCommentPost(selectedPost)" size="sm" variant="outline">💬 Comment</Button>
            <Button @click="handleRepostPost(selectedPost.post_id)" size="sm" variant="outline">↻ Repost</Button>
            <Button @click="handleSharePost(selectedPost.post_id)" size="sm" variant="outline">📤 Share</Button>
            <Button @click="handleQuotePost(selectedPost)" size="sm" variant="outline" class="col-span-2">📋 Quote</Button>
          </div>
        </Card>
      </div>

      <!-- Comment Section -->
      <Card>
        <h3 class="text-sm font-semibold text-gray-900 mb-3">💬 Comment</h3>
        <div class="space-y-3">
          <textarea
            v-model="commentText"
            rows="3"
            class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            placeholder="Type your comment here..."
          />
          <div class="flex items-center gap-2">
            <span class="text-xs text-gray-500">Templates:</span>
            <button
              v-for="template in commentTemplates"
              :key="template"
              @click="commentText = template"
              class="px-2 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50"
            >
              {{ template }}
            </button>
          </div>
          <Button @click="handleSubmitComment" :disabled="!commentText || !selectedPost" size="sm" variant="primary">
            📤 Post
          </Button>
        </div>
      </Card>

      <!-- User Interaction -->
      <Card>
        <h3 class="text-sm font-semibold text-gray-900 mb-3">👤 User Interaction</h3>
        <div class="flex gap-2">
          <input
            v-model="interactionUsername"
            type="text"
            class="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm"
            placeholder="@may__lily"
          />
          <Button @click="handleLoadUserStatus" :disabled="loading || !interactionUsername" :loading="loading">
            🔍 Load
          </Button>
        </div>
        <div v-if="userFollowStatus" class="mt-3">
          <div class="flex items-center gap-2">
            <span class="text-sm">Status:</span>
            <span v-if="userFollowStatus.isFollowing" class="text-sm font-medium text-green-600">Following ✓</span>
            <span v-else class="text-sm font-medium text-gray-500">Not Following</span>
            <Button @click="handleFollowUser(interactionUsername)" size="sm" variant="primary" class="ml-2">
              Follow
            </Button>
            <Button @click="handleUnfollowUser(interactionUsername)" size="sm" variant="outline">
              Unfollow
            </Button>
          </div>
        </div>
      </Card>

      <!-- Select User and Comment -->
      <Card>
        <h3 class="text-sm font-semibold text-gray-900 mb-4">🎯 Select User and Comment</h3>
        <div class="space-y-4">
          <!-- User Selection -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Select User from Feed</label>
            <select
              v-model="selectUserCommentConfig.username"
              :disabled="feedItems.length === 0"
              class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <option :value="null" disabled>Choose a user...</option>
              <option v-for="username in uniqueUsernames" :key="username" :value="username">
                @{{ username }}
              </option>
            </select>
            <p v-if="feedItems.length === 0" class="text-xs text-gray-500 mt-1">Load feed items first to see available users</p>
          </div>

          <!-- Filter Criteria -->
          <div class="border border-gray-200 rounded-lg p-4">
            <h4 class="text-sm font-medium text-gray-700 mb-3">Filter Criteria:</h4>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-xs text-gray-600 mb-1">Min Likes</label>
                <input v-model.number="selectUserCommentConfig.filter_criteria.min_likes" type="number" min="0" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm" />
              </div>
              <div>
                <label class="block text-xs text-gray-600 mb-1">Max Likes</label>
                <input v-model.number="selectUserCommentConfig.filter_criteria.max_likes" type="number" min="0" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm" />
              </div>
              <div>
                <label class="block text-xs text-gray-600 mb-1">Has Media</label>
                <select v-model="selectUserCommentConfig.filter_criteria.has_media" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm">
                  <option :value="null">All</option>
                  <option :value="true">Yes</option>
                  <option :value="false">No</option>
                </select>
              </div>
              <div>
                <label class="block text-xs text-gray-600 mb-1">Min Replies</label>
                <input v-model.number="selectUserCommentConfig.filter_criteria.min_replies" type="number" min="0" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm" />
              </div>
              <div>
                <label class="block text-xs text-gray-600 mb-1">Min Reposts</label>
                <input v-model.number="selectUserCommentConfig.filter_criteria.min_reposts" type="number" min="0" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm" />
              </div>
              <div>
                <label class="block text-xs text-gray-600 mb-1">Min Shares</label>
                <input v-model.number="selectUserCommentConfig.filter_criteria.min_shares" type="number" min="0" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm" />
              </div>
              <div>
                <label class="block text-xs text-gray-600 mb-1">Max Shares</label>
                <input v-model.number="selectUserCommentConfig.filter_criteria.max_shares" type="number" min="0" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm" />
              </div>
              <div>
                <label class="block text-xs text-gray-600 mb-1">Text Contains</label>
                <input v-model="selectUserCommentConfig.filter_criteria.text_contains" type="text" placeholder="Filter posts containing text..." class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm" />
              </div>
            </div>
            <p v-if="selectUserCommentConfig.filter_criteria.max_likes && selectUserCommentConfig.filter_criteria.min_likes && selectUserCommentConfig.filter_criteria.max_likes < selectUserCommentConfig.filter_criteria.min_likes" class="text-xs text-red-600 mt-2">
              Max likes must be >= Min likes
            </p>
            <p v-if="selectUserCommentConfig.filter_criteria.max_shares && selectUserCommentConfig.filter_criteria.min_shares && selectUserCommentConfig.filter_criteria.max_shares < selectUserCommentConfig.filter_criteria.min_shares" class="text-xs text-red-600 mt-2">
              Max shares must be >= Min shares
            </p>
          </div>

          <!-- Comment Settings -->
          <div class="border border-gray-200 rounded-lg p-4">
            <h4 class="text-sm font-medium text-gray-700 mb-3">Comment Settings:</h4>
            <div class="space-y-3">
              <div>
                <label class="block text-xs text-gray-600 mb-1">Max Posts to Comment</label>
                <input v-model.number="selectUserCommentConfig.max_posts_to_comment" type="number" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm" min="1" max="100" />
              </div>
              <div>
                <label class="flex items-center gap-2">
                  <input v-model="selectUserCommentConfig.random_selection" type="checkbox" class="rounded" />
                  <span class="text-xs text-gray-600">Random Selection</span>
                </label>
              </div>
              <div>
                <label class="block text-xs text-gray-600 mb-1">Comment Delay (ms)</label>
                <div class="flex gap-2">
                  <input v-model.number="selectUserCommentConfig.comment_delay_min" type="number" placeholder="Min" class="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm" min="1000" />
                  <input v-model.number="selectUserCommentConfig.comment_delay_max" type="number" placeholder="Max" class="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm" min="1000" />
                </div>
                <p v-if="selectUserCommentConfig.comment_delay_max < selectUserCommentConfig.comment_delay_min" class="text-xs text-red-600 mt-1">
                  Max delay must be >= Min delay
                </p>
              </div>
              <div>
                <label class="block text-xs text-gray-600 mb-1">Target URL (optional)</label>
                <input v-model="selectUserCommentConfig.target_url" type="text" placeholder="https://www.threads.net" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm" />
              </div>
              <div>
                <label class="block text-xs text-gray-600 mb-1">Max Items to Extract from Feed</label>
                <input v-model.number="selectUserCommentConfig.max_items" type="number" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm" min="1" max="500" />
              </div>
              <div>
                <label class="block text-xs text-gray-600 mb-1">Max Items from User Profile</label>
                <input v-model.number="selectUserCommentConfig.user_max_items" type="number" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm" min="1" max="500" />
                <p class="text-xs text-gray-500 mt-1">Maximum posts to extract from selected user's profile</p>
              </div>
              <div>
                <label class="block text-xs text-gray-600 mb-1">Comment Templates</label>
                <div class="flex flex-wrap gap-2">
                  <button
                    v-for="(template, idx) in selectUserCommentConfig.comment_templates"
                    :key="idx"
                    @click="selectUserCommentConfig.comment_templates.splice(idx, 1)"
                    class="px-2 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50"
                  >
                    {{ template }} ×
                  </button>
                  <button
                    @click="addSelectUserCommentTemplate"
                    class="px-2 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50 text-blue-600"
                  >
                    + Add Template
                  </button>
                </div>
              </div>
            </div>
          </div>

          <Button @click="handleSelectUserAndComment" :disabled="loading || !selectUserCommentConfig.username || feedItems.length === 0" :loading="loading" variant="primary" size="lg" class="w-full">
            🚀 Start Select User & Comment
          </Button>
        </div>

        <!-- Progress & Results -->
        <div v-if="selectUserCommentResults" class="mt-6 border-t border-gray-200 pt-4">
          <h4 class="text-sm font-semibold text-gray-900 mb-3">📊 Progress & Results</h4>
          <div class="space-y-3">
            <div>
              <div class="flex justify-between text-sm mb-1">
                <span>Status:</span>
                <span class="font-medium">{{ selectUserCommentResults.status || 'In Progress' }}</span>
              </div>
              <div class="w-full bg-gray-200 rounded-full h-2">
                <div
                  class="bg-primary-500 h-2 rounded-full transition-all"
                  :style="{ width: `${selectUserCommentProgress}%` }"
                ></div>
              </div>
              <div class="text-xs text-gray-600 mt-1">
                {{ selectUserCommentResults.totalCommented || 0 }} / {{ selectUserCommentConfig.max_posts_to_comment }} posts commented
              </div>
            </div>
            <div v-if="selectUserCommentResults.results && selectUserCommentResults.results.length > 0" class="space-y-2">
              <div class="text-sm font-medium">Results:</div>
              <div
                v-for="(result, idx) in selectUserCommentResults.results"
                :key="idx"
                class="p-2 rounded border text-sm"
                :class="result.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'"
              >
                <span :class="result.success ? 'text-green-600' : 'text-red-600'">
                  {{ result.success ? '✅' : '❌' }} @{{ result.username }} - {{ result.success ? 'Commented' : 'Failed' }}: "{{ result.comment }}"
                </span>
              </div>
            </div>
          </div>
        </div>
      </Card>
    </div>

    <!-- Tab: Browse & Comment -->
    <div v-else-if="activeTab === 'browse'" class="space-y-6">
      <!-- Configuration -->
      <Card>
        <h3 class="text-sm font-semibold text-gray-900 mb-4">⚙️ Configuration</h3>
        <div class="space-y-4">
          <!-- Filter Criteria -->
          <div class="border border-gray-200 rounded-lg p-4">
            <h4 class="text-sm font-medium text-gray-700 mb-3">Filter Criteria:</h4>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-xs text-gray-600 mb-1">Min Likes</label>
                <input v-model.number="browseConfig.filter_criteria.min_likes" type="number" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm" />
              </div>
              <div>
                <label class="block text-xs text-gray-600 mb-1">Max Likes</label>
                <input v-model.number="browseConfig.filter_criteria.max_likes" type="number" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm" />
              </div>
              <div>
                <label class="block text-xs text-gray-600 mb-1">Has Media</label>
                <select v-model="browseConfig.filter_criteria.has_media" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm">
                  <option :value="null">All</option>
                  <option :value="true">Yes</option>
                  <option :value="false">No</option>
                </select>
              </div>
              <div>
                <label class="block text-xs text-gray-600 mb-1">Min Replies</label>
                <input v-model.number="browseConfig.filter_criteria.min_replies" type="number" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm" />
              </div>
            </div>
          </div>

          <!-- Comment Settings -->
          <div class="border border-gray-200 rounded-lg p-4">
            <h4 class="text-sm font-medium text-gray-700 mb-3">Comment Settings:</h4>
            <div class="space-y-3">
              <div>
                <label class="block text-xs text-gray-600 mb-1">Target URL (optional)</label>
                <input v-model="browseConfig.target_url" type="text" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm" placeholder="https://www.threads.net (leave empty for default)" />
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-xs text-gray-600 mb-1">Max Posts to Comment</label>
                  <input v-model.number="browseConfig.max_posts_to_comment" type="number" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm" min="1" max="100" />
                </div>
                <div>
                  <label class="block text-xs text-gray-600 mb-1">Max Items to Extract</label>
                  <input v-model.number="browseConfig.max_items" type="number" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm" min="1" max="500" />
                </div>
              </div>
              <div>
                <label class="flex items-center gap-2">
                  <input v-model="browseConfig.random_selection" type="checkbox" class="rounded" />
                  <span class="text-xs text-gray-600">Random Selection</span>
                </label>
              </div>
              <div>
                <label class="block text-xs text-gray-600 mb-1">Comment Delay (ms)</label>
                <div class="flex gap-2">
                  <input v-model.number="browseConfig.comment_delay_min" type="number" placeholder="Min" class="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm" min="1000" />
                  <input v-model.number="browseConfig.comment_delay_max" type="number" placeholder="Max" class="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm" min="1000" />
                </div>
                <p v-if="browseConfig.comment_delay_max < browseConfig.comment_delay_min" class="text-xs text-red-600 mt-1">
                  Max delay must be >= Min delay
                </p>
              </div>
              <div>
                <label class="block text-xs text-gray-600 mb-1">Comment Templates</label>
                <div class="flex flex-wrap gap-2">
                  <button
                    v-for="(template, idx) in browseConfig.comment_templates"
                    :key="idx"
                    @click="browseConfig.comment_templates.splice(idx, 1)"
                    class="px-2 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50"
                  >
                    {{ template }} ×
                  </button>
                  <button
                    @click="addCommentTemplate"
                    class="px-2 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50 text-blue-600"
                  >
                    + Add Template
                  </button>
                </div>
              </div>
            </div>
          </div>

          <Button @click="handleBrowseAndComment" :disabled="loading" :loading="loading" variant="primary" size="lg" class="w-full">
            🚀 Start Browsing & Commenting
          </Button>
        </div>
      </Card>

      <!-- Progress & Results -->
      <Card v-if="browseResults">
        <h3 class="text-sm font-semibold text-gray-900 mb-3">📊 Progress & Results</h3>
        <div class="space-y-3">
          <div>
            <div class="flex justify-between text-sm mb-1">
              <span>Status:</span>
              <span class="font-medium">{{ browseResults.status || 'In Progress' }}</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div
                class="bg-primary-500 h-2 rounded-full transition-all"
                :style="{ width: `${browseProgress}%` }"
              ></div>
            </div>
            <div class="text-xs text-gray-600 mt-1">
              {{ browseResults.totalCommented || 0 }} / {{ browseConfig.max_posts_to_comment }} posts commented
            </div>
          </div>
          <div v-if="browseResults.results && browseResults.results.length > 0" class="space-y-2">
            <div class="text-sm font-medium">Results:</div>
            <div
              v-for="(result, idx) in browseResults.results"
              :key="idx"
              class="text-sm p-2 rounded border"
              :class="result.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'"
            >
              <span :class="result.success ? 'text-green-600' : 'text-red-600'">
                {{ result.success ? '✅' : '❌' }} @{{ result.username }} - {{ result.success ? 'Commented' : 'Failed' }}: "{{ result.comment }}"
              </span>
            </div>
          </div>
        </div>
      </Card>
    </div>

    <!-- Tab: Profiles -->
    <div v-if="activeTab === 'profiles'" class="space-y-6">
      <Card>
        <h3 class="text-lg font-semibold text-gray-900 mb-4">Profile Management</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Base Directory
            </label>
            <div class="flex gap-2">
              <input
                v-model="baseDirectoryOverride"
                type="text"
                class="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="/home/user/profiles"
              />
              <Button
                @click="handleListProfiles"
                :disabled="loading || !baseDirectoryOverride"
                :loading="loading"
                variant="primary"
              >
                List Profiles
              </Button>
            </div>
          </div>

          <div v-if="profileList && profileList.length > 0" class="space-y-2">
            <h4 class="text-sm font-medium text-gray-700">Profiles ({{ profileList.length }})</h4>
            <div class="space-y-2">
              <div
                v-for="profile in profileList"
                :key="profile.profile_id"
                class="p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer"
                @click="handleViewProfile(profile.profile_id)"
              >
                <div class="flex items-center justify-between">
                  <div>
                    <div class="font-medium text-sm text-gray-900">{{ profile.profile_id }}</div>
                    <div class="text-xs text-gray-500">{{ profile.full_path }}</div>
                  </div>
                  <div class="flex items-center gap-2">
                    <span v-if="profile.exists" class="text-xs text-green-600">✓ Exists</span>
                    <span v-else class="text-xs text-gray-400">✗ Missing</span>
                    <span v-if="profile.has_session" class="text-xs text-blue-600">Session</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="selectedProfile" class="border-t border-gray-200 pt-4">
            <h4 class="text-sm font-medium text-gray-700 mb-2">Profile Details</h4>
            <div class="space-y-2 text-sm">
              <div><span class="font-medium">Profile ID:</span> {{ selectedProfile.profile_id }}</div>
              <div><span class="font-medium">Path:</span> {{ selectedProfile.path }}</div>
              <div><span class="font-medium">Full Path:</span> {{ selectedProfile.full_path }}</div>
              <div><span class="font-medium">Exists:</span> {{ selectedProfile.exists ? 'Yes' : 'No' }}</div>
              <div v-if="selectedProfile.size"><span class="font-medium">Size:</span> {{ formatNumber(selectedProfile.size) }} bytes</div>
              <div><span class="font-medium">Has Session:</span> {{ selectedProfile.has_session ? 'Yes' : 'No' }}</div>
            </div>
          </div>
        </div>
      </Card>
    </div>

    <!-- Tab: Bulk Login -->
    <div v-if="activeTab === 'bulk-login'" class="space-y-6">
      <Card>
        <h3 class="text-lg font-semibold text-gray-900 mb-4">Bulk Login</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Base Directory
            </label>
            <input
              v-model="bulkLoginBaseDirectory"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="/home/user/profiles"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Accounts
            </label>
            <div class="space-y-2">
              <div
                v-for="(account, idx) in bulkLoginAccounts"
                :key="idx"
                class="flex gap-2 items-center p-2 border border-gray-200 rounded"
              >
                <input
                  v-model="account.username"
                  type="text"
                  placeholder="Username"
                  class="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm"
                />
                <input
                  v-model="account.password"
                  type="password"
                  placeholder="Password"
                  class="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm"
                />
                <input
                  v-model="account.account_id"
                  type="text"
                  placeholder="Account ID (optional)"
                  class="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm"
                />
                <button
                  @click="bulkLoginAccounts.splice(idx, 1)"
                  class="px-2 py-1 text-red-600 hover:bg-red-50 rounded"
                >
                  ×
                </button>
              </div>
              <Button
                @click="bulkLoginAccounts.push({ username: '', password: '', account_id: '' })"
                variant="outline"
                size="sm"
              >
                + Add Account
              </Button>
            </div>
          </div>

          <div>
            <label class="flex items-center gap-2">
              <input v-model="bulkLoginOptions.continue_on_error" type="checkbox" class="rounded" />
              <span class="text-sm text-gray-700">Continue on error</span>
            </label>
            <div class="mt-2">
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Delay between logins (ms)
              </label>
              <input
                v-model.number="bulkLoginOptions.delay_between_logins"
                type="number"
                class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                min="1000"
              />
            </div>
          </div>

          <Button
            @click="handleBulkLogin"
            :disabled="loading || !bulkLoginBaseDirectory || bulkLoginAccounts.length === 0"
            :loading="loading"
            variant="primary"
            size="lg"
            class="w-full"
          >
            Login All Accounts
          </Button>

          <div v-if="bulkLoginResults" class="border-t border-gray-200 pt-4">
            <h4 class="text-sm font-medium text-gray-700 mb-2">Results</h4>
            <div class="space-y-2">
              <div
                v-for="(result, idx) in bulkLoginResults.results || []"
                :key="idx"
                class="p-2 rounded border text-sm"
                :class="result.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'"
              >
                <span :class="result.success ? 'text-green-600' : 'text-red-600'">
                  {{ result.success ? '✅' : '❌' }} {{ result.username || result.account_id }}: {{ result.message || (result.success ? 'Success' : 'Failed') }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  </div>

  <!-- Media Gallery Modal -->
  <Teleport to="body">
    <Transition
      enter-active-class="transition-opacity duration-200"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition-opacity duration-200"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="showMediaGallery && selectedMediaItem"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75"
        @click.self="showMediaGallery = false"
      >
        <div class="relative max-w-4xl max-h-[90vh] w-full mx-4">
          <!-- Close Button -->
          <button
            @click="showMediaGallery = false"
            class="absolute top-4 right-4 z-10 p-2 bg-white bg-opacity-90 rounded-full hover:bg-opacity-100 transition-colors"
            title="Close (Esc)"
          >
            <svg class="w-6 h-6 text-gray-800" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>

          <!-- Navigation Buttons -->
          <button
            v-if="selectedMediaItem && selectedMediaItem.media_count > 1"
            @click="prevMedia"
            class="absolute left-4 top-1/2 -translate-y-1/2 z-10 p-3 bg-white bg-opacity-90 rounded-full hover:bg-opacity-100 transition-colors"
            title="Previous (←)"
          >
            <svg class="w-6 h-6 text-gray-800" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <button
            v-if="selectedMediaItem && selectedMediaItem.media_count > 1"
            @click="nextMedia"
            class="absolute right-4 top-1/2 -translate-y-1/2 z-10 p-3 bg-white bg-opacity-90 rounded-full hover:bg-opacity-100 transition-colors"
            title="Next (→)"
          >
            <svg class="w-6 h-6 text-gray-800" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>

          <!-- Media Container -->
          <div class="bg-white rounded-lg overflow-hidden">
            <!-- Media Counter -->
            <div v-if="selectedMediaItem && selectedMediaItem.media_count > 1" class="absolute top-4 left-4 z-10 px-3 py-1 bg-black bg-opacity-60 text-white text-sm rounded-full">
              {{ currentMediaIndex + 1 }} / {{ selectedMediaItem.media_count }}
            </div>

            <!-- Current Media -->
            <div class="flex items-center justify-center bg-black min-h-[400px]">
              <!-- Image Media -->
              <ImageMedia
                v-if="selectedMediaItem && getMediaTypeAtIndex(currentMediaIndex) === 1 && currentMediaIndex < selectedMediaItem.media_count"
                :key="`image-${selectedMediaItem.post_id}-${currentMediaIndex}`"
                :src="getMediaUrl(selectedMediaItem.post_id, currentMediaIndex, 'full')"
                :alt="`Media ${currentMediaIndex + 1} of ${selectedMediaItem.media_count}`"
                :width="800"
                :height="600"
                size="full"
                :lazy="false"
                :placeholder="true"
                container-class="max-w-full max-h-[90vh]"
                image-class="object-contain"
              />
              
              <!-- Video Media -->
              <VideoMedia
                v-else-if="selectedMediaItem && getMediaTypeAtIndex(currentMediaIndex) === 2 && currentMediaIndex < selectedMediaItem.media_count"
                :key="`video-${selectedMediaItem.post_id}-${currentMediaIndex}`"
                :src="getMediaUrl(selectedMediaItem.post_id, currentMediaIndex, 'full')"
                :poster="getMediaUrl(selectedMediaItem.post_id, currentMediaIndex, 'thumbnail')"
                :alt="`Video ${currentMediaIndex + 1} of ${selectedMediaItem.media_count}`"
                :width="800"
                :height="600"
                :preload="'metadata'"
                :autoplay="false"
                :show-controls="true"
                :lazy="false"
                :placeholder="true"
                container-class="max-w-full max-h-[90vh]"
              />
            </div>

            <!-- Thumbnail Navigation -->
            <div v-if="selectedMediaItem && selectedMediaItem.media_count > 1" class="p-4 bg-gray-100 flex gap-2 overflow-x-auto">
              <button
                v-for="index in selectedMediaItem.media_count"
                :key="`thumb-${index - 1}`"
                @click="currentMediaIndex = index - 1"
                class="flex-shrink-0 w-20 h-20 rounded overflow-hidden border-2 transition-all"
                :class="currentMediaIndex === index - 1 ? 'border-blue-500' : 'border-transparent hover:border-gray-400'"
              >
                <ImageMedia
                  :src="getMediaUrl(selectedMediaItem.post_id, index - 1, 'thumbnail')"
                  :alt="`Thumbnail ${index}`"
                  :width="80"
                  :height="80"
                  size="thumbnail"
                  :lazy="true"
                  :placeholder="true"
                  container-class="w-full h-full"
                  image-class="object-cover"
                />
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>

  <!-- Feed Insights Modal -->
  <FeedInsights
    v-model="showFeedInsights"
    :feed-items="feedItems"
  />
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick, Teleport } from 'vue'
import {
  RssIcon,
  ArrowPathIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  InformationCircleIcon
} from '@heroicons/vue/24/outline'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'
import Alert from '@/components/common/Alert.vue'
import Pagination from '@/components/common/Pagination.vue'
import ImageMedia from '@/components/common/ImageMedia.vue'
import VideoMedia from '@/components/common/VideoMedia.vue'
import FeedItem from '@/components/feed/FeedItem.vue'
import FeedInsights from '@/components/feed/FeedInsights.vue'
import { useFeed } from '@/features/feed/composables/useFeed'
import { useAccountsStore } from '@/stores/accounts'
import { useAccounts } from '@/features/accounts/composables/useAccounts'
import { useToast } from '@/core/composables/useToast'

const {
  loading,
  loadingStats,
  loadingFeed,
  error,
  feedItems,
  stats,
  filters,
  accountId: accountIdFromComposable,
  profilePath,
  currentPage,
  pageSize,
  totalItems,
  loadFeed,
  loadUserPosts,
  loadSavedFeed,
  loadPostHistory,
  loadStats: loadStatsOriginal,
  clearCache,
  likePost,
  commentOnPost,
  repostPost,
  sharePost,
  quotePost,
  followUser,
  unfollowUser,
  getUserFollowStatus,
  browseAndComment,
  selectUserAndComment,
  getFeedPost,
  listProfiles,
  getProfile,
  bulkLogin,
  commentUserPosts
} = useFeed()

// Wrapper for loadStats
const loadStats = async (options = {}) => {
  // Track this request
  const abortController = new AbortController()
  pendingStatsRequest = abortController
  
  try {
    // Call original loadStats
    const result = await loadStatsOriginal(options)
    pendingStatsRequest = null
    return result
  } catch (err) {
    pendingStatsRequest = null
    // If request was aborted, return default stats
    if (err.name === 'AbortError' || err.message?.includes('aborted')) {
      console.error('[DEBUG] Stats request was aborted')
      return {
        cache: { enabled: false, hasData: false },
        server: { qrtools_available: false },
        note: "Stats request was cancelled"
      }
    }
    throw err
  }
}

// Accounts management
const accountsStore = useAccountsStore()
const { fetchAccounts } = useAccounts()

// Create local accountId ref to avoid conflicts
const accountId = ref('')
const switchingAccount = ref(false)
const sessionStatus = ref('unknown') // 'active', 'loading', 'inactive', 'unknown'
const showAdvancedSettings = ref(false) // Toggle for Advanced Settings section
const profilePathOverride = ref(null) // User override for profile_path
const profileIdOverride = ref(null) // User override for profile_id
const baseDirectoryOverride = ref(null) // User override for base_directory
const profileDirOverride = ref(null) // User override for profile_dir (alias)
const showFeedInsights = ref(false) // Toggle for Feed Insights modal

const activeTab = ref('feed')
// Track pending stats requests to cancel them if needed
let pendingStatsRequest = null
const tabs = [
  { id: 'feed', label: 'Feed' },
  { id: 'user-posts', label: 'User Posts' },
  { id: 'interactions', label: 'Interactions' },
  { id: 'browse', label: 'Browse & Comment' },
  { id: 'profiles', label: 'Profiles' },
  { id: 'bulk-login', label: 'Bulk Login' }
]

const timeRange = ref('30')
const selectedUsername = ref('')
const selectedUser = ref(null)
const userPosts = ref([])
const interactionPostId = ref('')
const selectedPost = ref(null)
const commentText = ref('')
const commentTemplates = ['Nice post! 👍', 'Great content!', 'Thanks for sharing!', 'Interesting! 💡', 'Love this! ❤️']
const interactionUsername = ref('')
const userFollowStatus = ref(null)
// Media gallery state
const showMediaGallery = ref(false)
const selectedMediaItem = ref(null)
const currentMediaIndex = ref(0)
const browseConfig = ref({
  filter_criteria: {
    min_likes: null,
    max_likes: null,
    has_media: null,
    min_replies: null
  },
  max_posts_to_comment: 5,
  random_selection: true,
  comment_delay_min: 5000,
  comment_delay_max: 15000,
  comment_templates: ['Nice post! 👍', 'Great content!', 'Thanks for sharing!'],
  target_url: null,
  max_items: 50
})
const browseResults = ref(null)

// Select User and Comment
const selectUserCommentConfig = ref({
  username: null,
  filter_criteria: {
    min_likes: null,
    max_likes: null,
    has_media: null,
    min_replies: null,
    min_reposts: null,
    min_shares: null,
    max_shares: null,
    text_contains: null
  },
  max_posts_to_comment: 5,
  random_selection: true,
  comment_templates: ['Nice post! 👍', 'Great content!'],
  comment_delay_min: 5000,
  comment_delay_max: 15000,
  target_url: null,
  max_items: 50,
  user_max_items: 20
})
const selectUserCommentResults = ref(null)

// Comment User Posts
const userCommentPostsConfig = ref({
  filter_criteria: {
    min_likes: null,
    max_likes: null,
    has_media: null,
    min_replies: null
  },
  max_posts_to_comment: 5,
  random_selection: true,
  comment_templates: ['Nice post! 👍', 'Great content!'],
  comment_delay_min: 5000,
  comment_delay_max: 15000,
  max_items: 50
})
const userCommentPostsResults = ref(null)

// Feed Stats (from backend metadata)
const feedStats = ref({
  total: 0,
  filtered: 0,
  showing: 0
})

// Profile Management
const profileList = ref([])
const selectedProfile = ref(null)

// Bulk Login
const bulkLoginBaseDirectory = ref('')
const bulkLoginAccounts = ref([{ username: '', password: '', account_id: '' }])
const bulkLoginOptions = ref({
  continue_on_error: true,
  delay_between_logins: 5000
})
const bulkLoginResults = ref(null)

// Computed
const availableAccounts = computed(() => {
  // Only return accounts from store, no fallback
  return accountsStore.accounts || []
})

// Get current account object
const currentAccount = computed(() => {
  if (!accountId.value) return null
  return accountsStore.accountById(accountId.value) || null
})

// Get profile_path from account metadata (with override support)
const currentProfilePath = computed(() => {
  // User override takes highest priority
  if (profilePathOverride.value) {
    return profilePathOverride.value
  }
  // Then from account metadata
  if (currentAccount.value) {
    const metadataPath = currentAccount.value.profile_path || 
                         currentAccount.value.metadata?.profile_path
    if (metadataPath) {
      return metadataPath
    }
    // If no profile_path in metadata, generate from account_id
    // Format: profiles/{account_id} (relative path, backend will normalize to absolute)
    if (accountId.value) {
      return `profiles/${accountId.value}`
    }
  }
  // Then from composable state
  if (profilePath.value) {
    return profilePath.value
  }
  // Fallback: generate from accountId if available
  if (accountId.value) {
    return `profiles/${accountId.value}`
  }
  return null
})

const sessionStatusText = computed(() => {
  switch (sessionStatus.value) {
    case 'active':
      return 'Active'
    case 'loading':
      return 'Loading...'
    case 'inactive':
      return 'Inactive'
    default:
      return 'Unknown'
  }
})

const filteredCount = computed(() => {
  // Return filtered count from backend metadata
  return feedStats.value.filtered || feedItems.value.length
})

// Check if any filters are active
const hasActiveFilters = computed(() => {
  return !!(
    (filters.value.min_likes !== null && filters.value.min_likes !== undefined) ||
    (filters.value.max_likes !== null && filters.value.max_likes !== undefined) ||
    (filters.value.min_replies !== null && filters.value.min_replies !== undefined) ||
    (filters.value.has_media !== null && filters.value.has_media !== undefined) ||
    filters.value.username ||
    filters.value.text_contains
  )
})

const averageLikes = computed(() => {
  if (userPosts.value.length === 0) return 0
  const total = userPosts.value.reduce((sum, post) => sum + (post.like_count || 0), 0)
  return Math.round(total / userPosts.value.length)
})

const averageReplies = computed(() => {
  if (userPosts.value.length === 0) return 0
  const total = userPosts.value.reduce((sum, post) => sum + (post.reply_count || 0), 0)
  return Math.round(total / userPosts.value.length)
})

const browseProgress = computed(() => {
  if (!browseResults.value || !browseConfig.value.max_posts_to_comment) return 0
  return Math.round((browseResults.value.totalCommented || 0) / browseConfig.value.max_posts_to_comment * 100)
})

// Unique usernames from feedItems for dropdown
const uniqueUsernames = computed(() => {
  const usernames = new Set()
  feedItems.value.forEach(item => {
    if (item.username) {
      usernames.add(item.username)
    }
  })
  return Array.from(usernames).sort()
})

// Progress for select user comment
const selectUserCommentProgress = computed(() => {
  if (!selectUserCommentResults.value || !selectUserCommentConfig.value.max_posts_to_comment) return 0
  return Math.round((selectUserCommentResults.value.totalCommented || 0) / selectUserCommentConfig.value.max_posts_to_comment * 100)
})

// Progress for user comment posts
const userCommentPostsProgress = computed(() => {
  if (!userCommentPostsResults.value || !userCommentPostsConfig.value.max_posts_to_comment) return 0
  return Math.round((userCommentPostsResults.value.totalCommented || 0) / userCommentPostsConfig.value.max_posts_to_comment * 100)
})

// Methods
const formatNumber = (num) => {
  if (!num) return '0'
  return new Intl.NumberFormat('en-US').format(num)
}

const formatTimeAgo = (timestamp) => {
  if (!timestamp) return 'N/A'
  
  try {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now - date
    const diffSecs = Math.floor(diffMs / 1000)
    const diffMins = Math.floor(diffSecs / 60)
    const diffHours = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHours / 24)
    
    if (diffSecs < 60) return `${diffSecs}s ago`
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    
    return date.toLocaleDateString()
  } catch (err) {
    return 'N/A'
  }
}

// Load cached feed from database (replaces handleLoadSavedFeed)
const handleLoadCachedFeed = async (page = null) => {
  if (!accountId.value) {
    console.log(`[FeedExplorer] handleLoadCachedFeed: No accountId, skipping`)
    return
  }
  
  try {
    // Use provided page or current page
    const targetPage = page !== null ? page : currentPage.value
    const offset = (targetPage - 1) * pageSize.value
    
    console.log(`[FeedExplorer] handleLoadCachedFeed: Loading cached feed from database (account: ${accountId.value}, page: ${targetPage}, pageSize: ${pageSize.value}, offset: ${offset})`)
    
    // Build filters object from filter state
    const filterObj = {}
    if (filters.value.min_likes !== null && filters.value.min_likes !== undefined) {
      filterObj.min_likes = filters.value.min_likes
    }
    if (filters.value.max_likes !== null && filters.value.max_likes !== undefined) {
      filterObj.max_likes = filters.value.max_likes
    }
    if (filters.value.min_replies !== null && filters.value.min_replies !== undefined) {
      filterObj.min_replies = filters.value.min_replies
    }
    if (filters.value.has_media !== null && filters.value.has_media !== undefined) {
      filterObj.has_media = filters.value.has_media
    }
    if (filters.value.username) {
      filterObj.username = filters.value.username
    }
    if (filters.value.text_contains) {
      filterObj.text_contains = filters.value.text_contains
    }
    
    const result = await loadSavedFeed({ 
      account_id: accountId.value,
      limit: pageSize.value,
      offset: offset,
      filters: Object.keys(filterObj).length > 0 ? filterObj : undefined
    })
    
    // Update feedStats from metadata
    // Note: loadSavedFeed already updates feedItems.value internally
    if (result) {
      // Use result.total and result.filtered_total (already handled in loadSavedFeed)
      feedStats.value.total = result.total || 0
      feedStats.value.filtered = result.filtered_total !== undefined ? result.filtered_total : result.total || 0
      feedStats.value.showing = feedItems.value.length
      
      console.log(`[FeedExplorer] handleLoadCachedFeed: Stats updated from metadata:`, {
        total: feedStats.value.total,
        filtered: feedStats.value.filtered,
        showing: feedStats.value.showing,
        result_total: result.total,
        result_filtered_total: result.filtered_total,
        result_meta: result.meta
      })
    } else {
      // Last resort fallback - should not happen if backend is working correctly
      feedStats.value.total = feedItems.value.length
      feedStats.value.filtered = feedItems.value.length
      feedStats.value.showing = feedItems.value.length
      console.warn(`[FeedExplorer] handleLoadCachedFeed: No result returned from loadSavedFeed, using items.length as fallback`)
    }
    
    console.log(`[FeedExplorer] handleLoadCachedFeed: Successfully loaded ${feedItems.value.length} cached feed items`)
    console.log(`[FeedExplorer] handleLoadCachedFeed: Final Stats - Total: ${feedStats.value.total}, Filtered: ${feedStats.value.filtered}, Showing: ${feedStats.value.showing}`)
    
    if (feedItems.value.length === 0) {
      console.warn(`[FeedExplorer] handleLoadCachedFeed: No items found in database for account ${accountId.value}`)
      console.warn(`[FeedExplorer] handleLoadCachedFeed: This might mean:`)
      console.warn(`[FeedExplorer] handleLoadCachedFeed: 1. No data has been saved to database yet`)
      console.warn(`[FeedExplorer] handleLoadCachedFeed: 2. Account ID mismatch between frontend and database`)
      console.warn(`[FeedExplorer] handleLoadCachedFeed: 3. API endpoint returned empty array`)
    }
  } catch (err) {
    console.error('[FeedExplorer] handleLoadCachedFeed: Failed to load cached feed:', err)
    console.error('[FeedExplorer] handleLoadCachedFeed: Error details:', {
      message: err.message,
      stack: err.stack,
      response: err.response?.data
    })
    toast.error('Failed to load cached feed', err.message || 'Unknown error occurred')
  }
}

// Handle pagination page change
const handlePageChange = (page) => {
  console.log(`[FeedExplorer] handlePageChange: Changing to page ${page}`)
  currentPage.value = page
  handleLoadCachedFeed(page)
}

// Handle page size change
const handlePageSizeChange = (newSize) => {
  console.log(`[FeedExplorer] handlePageSizeChange: Changing page size to ${newSize}`)
  pageSize.value = newSize
  currentPage.value = 1 // Reset to first page
  handleLoadCachedFeed(1)
}

// Tab click handler
const handleTabClick = (tabId) => {
  // Change the tab (this will trigger watch(activeTab))
  activeTab.value = tabId
}

const handleViewPostHistory = async (postId) => {
  if (!postId || !accountId.value) {
    return
  }
  
  try {
    console.log(`[FeedExplorer] Loading post history for post: ${postId}`)
    const history = await loadPostHistory(postId, { 
      account_id: accountId.value
    })
    console.log(`[FeedExplorer] Post history:`, history)
    // TODO: Show history in modal or sidebar
    toast.info(`Post history: ${history.length} records found. Check console for details.`)
  } catch (err) {
    console.error('Failed to load post history:', err)
    toast.error('Failed to load post history', err.message || 'Unknown error occurred')
  }
}

const handleLoadFeed = async () => {
  try {
    // Sync local accountId and profilePath to composable
    accountIdFromComposable.value = accountId.value
    profilePath.value = currentProfilePath.value
    
    // Fetch new feed from Qrtools (will auto-save to DB)
    // feedItems.value will be automatically updated by loadFeed() composable
    await loadFeed({ 
      account_id: accountId.value,
      profile_path: profilePathOverride.value || currentProfilePath.value,
      profile_dir: profileDirOverride.value,
      profile_id: profileIdOverride.value,
      base_directory: baseDirectoryOverride.value
    })
    
    // NOTE: Do NOT auto-load stats after fetching feed
    // Stats should ONLY be loaded when user explicitly clicks "Refresh Status" button
    // This prevents browser from opening unnecessarily
    
    // Note: feedItems.value is already updated by loadFeed() composable
    // The new data is automatically saved to DB by backend auto-save
    console.log(`[FeedExplorer] Feed refreshed: ${feedItems.value.length} items loaded and saved to database`)
  } catch (err) {
    console.error('Failed to load feed:', err)
    toast.error('Failed to refresh feed', err.message || 'Unknown error occurred')
  }
}

const handleClearCache = async () => {
  try {
    await clearCache(null, { 
      account_id: accountId.value,
      profile_path: currentProfilePath.value
    })
    await handleLoadFeed()
  } catch (err) {
    console.error('Failed to clear cache:', err)
    toast.error('Failed to clear cache', err.message || 'Unknown error occurred')
  }
}

const handleLoadStats = async () => {
  // #region agent log
  const stackTrace = new Error().stack
  const logData = {
    location: 'FeedExplorer.vue:handleLoadStats',
    message: 'handleLoadStats CALLED - THIS OPENS BROWSER',
    data: {
      accountId: accountId.value,
      activeTab: activeTab.value,
      isMounted: isMounted.value,
      stackTrace: stackTrace?.split('\n').slice(0,10).join(' | ')
    },
    timestamp: Date.now(),
    sessionId: 'debug-session',
    runId: 'run1',
    hypothesisId: 'B'
  }
  console.error('[DEBUG] handleLoadStats CALLED:', logData)
  fetch('http://127.0.0.1:7251/ingest/51f0fb7e-17cd-490d-9237-943abd387122',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(logData)}).catch(()=>{});
  // #endregion
  
  if (!accountId.value) {
    // #region agent log
    fetch('http://127.0.0.1:7251/ingest/51f0fb7e-17cd-490d-9237-943abd387122',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'FeedExplorer.vue:handleLoadStats',message:'handleLoadStats early return - no accountId',data:{accountId:accountId.value},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'})}).catch(()=>{});
    // #endregion
    return
  }
  
  try {
    sessionStatus.value = 'loading'
    const profilePath = currentProfilePath.value
    // #region agent log
    fetch('http://127.0.0.1:7251/ingest/51f0fb7e-17cd-490d-9237-943abd387122',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'FeedExplorer.vue:handleLoadStats',message:'About to call loadStats - THIS WILL OPEN BROWSER',data:{accountId:accountId.value,profilePath,activeTab:activeTab.value},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'})}).catch(()=>{});
    // #endregion
    console.log(`[FeedExplorer] Loading stats for account: ${accountId.value}, profile_path: ${profilePath}`)
    await loadStats({ 
      account_id: accountId.value,
      profile_path: profilePath
    })
    
    // Log stats response for debugging
    console.log(`[FeedExplorer] Stats response:`, stats.value)
    console.log(`[FeedExplorer] Cache enabled:`, stats.value?.cache?.enabled)
    
    // Update session status based on stats
    if (stats.value?.cache?.enabled) {
      sessionStatus.value = 'active'
    } else {
      sessionStatus.value = 'inactive'
    }
  } catch (err) {
    console.error('Failed to load stats:', err)
    sessionStatus.value = 'inactive'
    toast.error('Failed to check session status', err.message || 'Unknown error occurred')
  }
}

const handleLoadUserPosts = async () => {
  if (!selectedUsername.value) return
  try {
    await loadUserPosts(selectedUsername.value, {
      account_id: accountId.value,
      profile_path: currentProfilePath.value
    })
    if (feedItems.value.length > 0) {
      selectedUser.value = feedItems.value[0]
      userPosts.value = feedItems.value
    }
  } catch (err) {
    console.error('Failed to load user posts:', err)
    toast.error('Failed to load user posts', err.message || 'Unknown error occurred')
  }
}

const handleLoadPost = async () => {
  if (!interactionPostId.value) return
  try {
    const result = await getFeedPost(interactionPostId.value)
    selectedPost.value = result.data || result
  } catch (err) {
    console.error('Failed to load post:', err)
    toast.error('Failed to load post', err.message || 'Unknown error occurred')
  }
}

const handleLikePost = async (postId) => {
  try {
    await likePost(postId, {
      account_id: accountId.value,
      profile_path: currentProfilePath.value
    })
    await handleLoadFeed()
  } catch (err) {
    console.error('Failed to like post:', err)
    toast.error('Failed to like post', err.message || 'Unknown error occurred')
  }
}

const handleCommentPost = async (post) => {
  if (!commentText.value && post) {
    // Open comment modal or focus textarea
    commentText.value = ''
    selectedPost.value = post
    activeTab.value = 'interactions'
    return
  }
  if (!selectedPost.value || !commentText.value) return
  try {
    await commentOnPost(selectedPost.value.post_id, commentText.value, {
      account_id: accountId.value,
      profile_path: currentProfilePath.value
    })
    commentText.value = ''
    await handleLoadFeed()
  } catch (err) {
    console.error('Failed to comment on post:', err)
    toast.error('Failed to comment on post', err.message || 'Unknown error occurred')
  }
}

const handleSubmitComment = async () => {
  await handleCommentPost(selectedPost.value)
}

const handleRepostPost = async (postId) => {
  try {
    await repostPost(postId, {
      account_id: accountId.value,
      profile_path: currentProfilePath.value
    })
    await handleLoadFeed()
  } catch (err) {
    console.error('Failed to repost:', err)
    toast.error('Failed to repost', err.message || 'Unknown error occurred')
  }
}

const handleSharePost = async (postId) => {
  try {
    await sharePost(postId, 'copy', {
      account_id: accountId.value,
      profile_path: currentProfilePath.value
    })
  } catch (err) {
    console.error('Failed to share post:', err)
    toast.error('Failed to share post', err.message || 'Unknown error occurred')
  }
}

const handleQuotePost = async (post) => {
  if (!commentText.value) {
    commentText.value = ''
    selectedPost.value = post
    activeTab.value = 'interactions'
    return
  }
  try {
    await quotePost(post.post_id, commentText.value, {
      account_id: accountId.value,
      profile_path: currentProfilePath.value
    })
    commentText.value = ''
    await handleLoadFeed()
  } catch (err) {
    console.error('Failed to quote post:', err)
    toast.error('Failed to quote post', err.message || 'Unknown error occurred')
  }
}

const handleFollowUser = async (username) => {
  try {
    await followUser(username, {
      account_id: accountId.value,
      profile_path: currentProfilePath.value
    })
    await handleLoadUserStatus()
  } catch (err) {
    console.error('Failed to follow user:', err)
    toast.error('Failed to follow user', err.message || 'Unknown error occurred')
  }
}

const handleUnfollowUser = async (username) => {
  try {
    await unfollowUser(username, {
      account_id: accountId.value,
      profile_path: currentProfilePath.value
    })
    await handleLoadUserStatus()
  } catch (err) {
    console.error('Failed to unfollow user:', err)
    toast.error('Failed to unfollow user', err.message || 'Unknown error occurred')
  }
}

const handleLoadUserStatus = async () => {
  if (!interactionUsername.value) return
  try {
    const result = await getUserFollowStatus(interactionUsername.value, {
      account_id: accountId.value,
      profile_path: currentProfilePath.value
    })
    userFollowStatus.value = result.data || result
  } catch (err) {
    console.error('Failed to load user status:', err)
    toast.error('Failed to load user status', err.message || 'Unknown error occurred')
  }
}

const handleBrowseAndComment = async () => {
  try {
    const configWithProfilePath = {
      ...browseConfig.value,
      profile_path: currentProfilePath.value
    }
    const result = await browseAndComment(configWithProfilePath, {
      account_id: accountId.value,
      profile_path: currentProfilePath.value
    })
    browseResults.value = result.data || result
  } catch (err) {
    console.error('Failed to browse and comment:', err)
    toast.error('Failed to browse and comment', err.message || 'Unknown error occurred')
  }
}

const addCommentTemplate = () => {
  const template = prompt('Enter comment template:')
  if (template) {
    browseConfig.value.comment_templates.push(template)
  }
}

const handleSelectUserAndComment = async () => {
  if (!selectUserCommentConfig.value.username) {
    toast.warning('Please select a username')
    return
  }
  if (!selectUserCommentConfig.value.max_posts_to_comment || selectUserCommentConfig.value.max_posts_to_comment <= 0) {
    toast.warning('Please set max posts to comment (must be > 0)')
    return
  }
  if (!selectUserCommentConfig.value.comment_templates || selectUserCommentConfig.value.comment_templates.length === 0) {
    toast.warning('Please add at least one comment template')
    return
  }
  if (selectUserCommentConfig.value.comment_delay_max < selectUserCommentConfig.value.comment_delay_min) {
    toast.warning('Comment delay max must be >= comment delay min')
    return
  }
  
  // Validate filter criteria
  if (selectUserCommentConfig.value.filter_criteria.max_likes && 
      selectUserCommentConfig.value.filter_criteria.min_likes &&
      selectUserCommentConfig.value.filter_criteria.max_likes < selectUserCommentConfig.value.filter_criteria.min_likes) {
    toast.warning('Max likes must be >= Min likes')
    return
  }
  if (selectUserCommentConfig.value.filter_criteria.max_shares && 
      selectUserCommentConfig.value.filter_criteria.min_shares &&
      selectUserCommentConfig.value.filter_criteria.max_shares < selectUserCommentConfig.value.filter_criteria.min_shares) {
    toast.warning('Max shares must be >= Min shares')
    return
  }
  
  try {
    // Convert to camelCase format for API (backend accepts both, but camelCase matches API docs)
    const configToSend = {
      username: selectUserCommentConfig.value.username,
      filterCriteria: selectUserCommentConfig.value.filter_criteria.min_likes !== null || 
                      selectUserCommentConfig.value.filter_criteria.max_likes !== null ||
                      selectUserCommentConfig.value.filter_criteria.has_media !== null ||
                      selectUserCommentConfig.value.filter_criteria.min_replies !== null ||
                      selectUserCommentConfig.value.filter_criteria.min_reposts !== null ||
                      selectUserCommentConfig.value.filter_criteria.min_shares !== null ||
                      selectUserCommentConfig.value.filter_criteria.max_shares !== null ||
                      selectUserCommentConfig.value.filter_criteria.text_contains !== null
        ? {
            min_likes: selectUserCommentConfig.value.filter_criteria.min_likes,
            max_likes: selectUserCommentConfig.value.filter_criteria.max_likes,
            has_media: selectUserCommentConfig.value.filter_criteria.has_media,
            min_replies: selectUserCommentConfig.value.filter_criteria.min_replies,
            min_reposts: selectUserCommentConfig.value.filter_criteria.min_reposts,
            min_shares: selectUserCommentConfig.value.filter_criteria.min_shares,
            max_shares: selectUserCommentConfig.value.filter_criteria.max_shares,
            text_contains: selectUserCommentConfig.value.filter_criteria.text_contains || undefined
          }
        : undefined,
      maxPostsToComment: selectUserCommentConfig.value.max_posts_to_comment,
      randomSelection: selectUserCommentConfig.value.random_selection,
      commentTemplates: selectUserCommentConfig.value.comment_templates,
      commentDelayMin: selectUserCommentConfig.value.comment_delay_min,
      commentDelayMax: selectUserCommentConfig.value.comment_delay_max,
      targetUrl: selectUserCommentConfig.value.target_url || undefined,
      maxItems: selectUserCommentConfig.value.max_items || undefined,
      userMaxItems: selectUserCommentConfig.value.user_max_items || undefined,
      profile_path: currentProfilePath.value
    }
    
    // Remove undefined/null values to clean up the request
    Object.keys(configToSend).forEach(key => {
      if (configToSend[key] === undefined || configToSend[key] === null) {
        delete configToSend[key]
      }
    })
    if (configToSend.filterCriteria) {
      Object.keys(configToSend.filterCriteria).forEach(key => {
        if (configToSend.filterCriteria[key] === undefined || configToSend.filterCriteria[key] === null) {
          delete configToSend.filterCriteria[key]
        }
      })
      if (Object.keys(configToSend.filterCriteria).length === 0) {
        delete configToSend.filterCriteria
      }
    }
    
    const result = await selectUserAndComment(configToSend, {
      account_id: accountId.value,
      profile_path: currentProfilePath.value
    })
    selectUserCommentResults.value = result.data || result
    toast.success('Select user and comment started successfully!')
  } catch (err) {
    console.error('Failed to select user and comment:', err)
    toast.error(`Failed: ${err.message || 'Unknown error'}`)
  }
}

const handleCommentUserPosts = async () => {
  if (!selectedUsername.value) {
    toast.warning('Please enter a username')
    return
  }
  if (!userCommentPostsConfig.value.max_posts_to_comment || userCommentPostsConfig.value.max_posts_to_comment <= 0) {
    toast.warning('Please set max posts to comment (must be > 0)')
    return
  }
  if (!userCommentPostsConfig.value.comment_templates || userCommentPostsConfig.value.comment_templates.length === 0) {
    toast.warning('Please add at least one comment template')
    return
  }
  if (userCommentPostsConfig.value.comment_delay_max < userCommentPostsConfig.value.comment_delay_min) {
    toast.warning('Comment delay max must be >= comment delay min')
    return
  }
  try {
    const configWithProfilePath = {
      ...userCommentPostsConfig.value,
      profile_path: currentProfilePath.value
    }
    const result = await commentUserPosts(selectedUsername.value, configWithProfilePath, {
      account_id: accountId.value,
      profile_path: currentProfilePath.value
    })
    userCommentPostsResults.value = result.data || result
  } catch (err) {
    console.error('Failed to comment user posts:', err)
    toast.error(`Failed: ${err.message || 'Unknown error'}`)
  }
}

const addSelectUserCommentTemplate = () => {
  const template = prompt('Enter comment template:')
  if (template) {
    selectUserCommentConfig.value.comment_templates.push(template)
  }
}

const addUserCommentPostsTemplate = () => {
  const template = prompt('Enter comment template:')
  if (template) {
    userCommentPostsConfig.value.comment_templates.push(template)
  }
}

// Handle viewing media gallery - open modal to view all media
// Helper function to get media URL with optional size parameter
const getMediaUrl = (postId, index, size = 'full') => {
  const baseUrl = `/api/feed/media/${postId}/${index}`
  const params = size === 'thumbnail' ? '?w=200&h=200' : ''
  return `${baseUrl}${params}`
}

// Helper function to get avatar URL with optional size parameter
const getAvatarUrl = (userId, size = 'thumbnail') => {
  const baseUrl = `/api/feed/avatar/${userId}`
  const params = size === 'thumbnail' ? '?w=56&h=56' : ''
  return `${baseUrl}${params}`
}

// Detect media type per index (handles mixed media: images + videos)
// Note: Backend FeedItemResponse excludes media_urls, so we can't detect from original CDN URLs.
// For API endpoint URLs (/api/feed/media/{postId}/{index}), we fallback to feed item's media_type.
// This works correctly for single-type media items, but may be imperfect for mixed media.
// TODO: Backend enhancement - add media_types array to FeedItemResponse for accurate per-media-type detection
const getMediaTypeAtIndex = (index) => {
  if (!selectedMediaItem.value || index < 0 || index >= selectedMediaItem.value.media_count) {
    return 1 // Default to image
  }
  
  // Try to detect from media_urls if available (may not be present in FeedItemResponse)
  const mediaUrls = selectedMediaItem.value.media_urls || []
  if (mediaUrls[index]) {
    const url = String(mediaUrls[index]).toLowerCase()
    
    // Video indicators: file extensions and URL patterns
    if (url.match(/\.(mp4|mov|webm|m4v)(\?|$)/i) || 
        url.includes('/video/') || 
        (url.includes('video') && !url.includes('image')) ||
        url.includes('.mp4') ||
        url.includes('.mov') ||
        url.includes('.webm')) {
      return 2 // video
    }
    
    // Image indicators: file extensions and URL patterns
    if (url.match(/\.(jpg|jpeg|png|gif|webp)(\?|$)/i) || 
        url.includes('/image/') || 
        (url.includes('image') && !url.includes('video')) ||
        url.includes('.jpg') ||
        url.includes('.jpeg') ||
        url.includes('.png') ||
        url.includes('.gif') ||
        url.includes('.webp')) {
      return 1 // image
    }
  }
  
  // Fallback: Use feed item's media_type
  // This handles API endpoint URLs without extensions (/api/feed/media/{postId}/{index})
  // LIMITATION: For mixed media (e.g., 2 images + 1 video), this will use the single media_type
  // value for all media items, which may be incorrect. Backend enhancement needed for accurate detection.
  return selectedMediaItem.value.media_type || 1
}

const handleViewMedia = (item) => {
  if (!item || !item.media_count || item.media_count === 0) {
    console.warn('[FeedExplorer] handleViewMedia: No media found for item:', item)
    return
  }
  
  // If only 1 media, open directly in new tab
  if (item.media_count === 1) {
    window.open(getMediaUrl(item.post_id, 0), '_blank', 'noopener,noreferrer')
    return
  }
  
  // If multiple media, open gallery modal
  selectedMediaItem.value = item
  currentMediaIndex.value = 0
  showMediaGallery.value = true
}

// Navigate to next media in gallery
const nextMedia = () => {
  if (selectedMediaItem.value && selectedMediaItem.value.media_count) {
    currentMediaIndex.value = (currentMediaIndex.value + 1) % selectedMediaItem.value.media_count
  }
}

// Navigate to previous media in gallery
const prevMedia = () => {
  if (selectedMediaItem.value && selectedMediaItem.value.media_count) {
    currentMediaIndex.value = currentMediaIndex.value === 0 
      ? selectedMediaItem.value.media_count - 1 
      : currentMediaIndex.value - 1
  }
}

const handleViewPost = (item) => {
  window.open(item.post_url, '_blank')
}

// Note: Error handling is now done by ImageMedia and VideoMedia components

const handleListProfiles = async () => {
  if (!baseDirectoryOverride.value) {
    return
  }
  try {
    const response = await listProfiles(baseDirectoryOverride.value)
    profileList.value = response.profiles || response.data?.profiles || []
  } catch (err) {
    console.error('Failed to list profiles:', err)
    toast.error('Failed to list profiles', err.message || 'Unknown error occurred')
  }
}

const handleViewProfile = async (profileId) => {
  if (!baseDirectoryOverride.value) {
    return
  }
  try {
    const response = await getProfile(profileId, baseDirectoryOverride.value)
    selectedProfile.value = response || response.data
  } catch (err) {
    console.error('Failed to get profile:', err)
    toast.error('Failed to get profile', err.message || 'Unknown error occurred')
  }
}

const handleBulkLogin = async () => {
  if (!bulkLoginBaseDirectory.value || bulkLoginAccounts.value.length === 0) {
    return
  }
  try {
    const accounts = bulkLoginAccounts.value.filter(acc => acc.username && acc.password)
    if (accounts.length === 0) {
      toast.warning('Please provide at least one account with username and password')
      return
    }
    const response = await bulkLogin({
      base_directory: bulkLoginBaseDirectory.value,
      accounts: accounts,
      options: bulkLoginOptions.value
    })
    bulkLoginResults.value = response || response.data
  } catch (err) {
    console.error('Failed to bulk login:', err)
    toast.error('Failed to bulk login', err.message || 'Unknown error occurred')
  }
}

const handleAccountChange = async () => {
  if (!accountId.value) {
    return
  }
  
  // CRITICAL: Do NOT load stats automatically when account changes
  // Stats should ONLY be loaded when user explicitly clicks "Refresh Status" button
  // This prevents browser from opening automatically when:
  // 1. Component mounts and sets default account
  // 2. User switches account from dropdown
  // 3. Account is changed programmatically
  
  console.log(`[FeedExplorer] Account changed to: ${accountId.value}`)
  
  // Set switching state
  switchingAccount.value = true
  // Set session status to unknown (user must click "Refresh Status" to check)
  sessionStatus.value = 'unknown'
  
  try {
    // Sync local accountId and profilePath to composable
    accountIdFromComposable.value = accountId.value
    const profilePathValue = currentProfilePath.value
    profilePath.value = profilePathValue
    
    console.log(`[FeedExplorer] Account changed to: ${accountId.value}, profile_path: ${profilePathValue}`)
    
    // Clear current data
    feedItems.value = []
    userPosts.value = []
    selectedUser.value = null
    selectedPost.value = null
    
    // NEVER auto-load stats - stats should ONLY be loaded when user explicitly clicks "Refresh Status" button
    // This prevents browser from opening automatically
    
    // Auto-load cached feed if on feed tab
    if (activeTab.value === 'feed' && isMounted.value) {
      await handleLoadCachedFeed()
    }
  } catch (err) {
    console.error('Failed to switch account:', err)
    sessionStatus.value = 'unknown'
    toast.error('Failed to switch account', err.message || 'Unknown error occurred')
  } finally {
    switchingAccount.value = false
  }
}

// Track if component is mounted to prevent auto-trigger on initial mount
const isMounted = ref(false)

// Track pending saved feed request to cancel if needed
let pendingSavedFeedRequest = null

// Watch activeTab changes to auto-load cached feed when switching to feed tab
watch(activeTab, async (newTab, oldTab) => {
  console.log(`[FeedExplorer] Tab changed: ${oldTab} → ${newTab}`)
  
  // Cancel any pending saved feed request when switching away from feed tab
  if (oldTab === 'feed' && newTab !== 'feed' && pendingSavedFeedRequest) {
    console.log(`[FeedExplorer] Cancelling pending saved feed request`)
    pendingSavedFeedRequest.abort()
    pendingSavedFeedRequest = null
  }
  
  // Auto-load cached feed when switching to feed tab
  if (newTab === 'feed' && accountId.value && isMounted.value) {
    console.log(`[FeedExplorer] Auto-loading cached feed from database`)
    
    // Cancel any existing pending request
    if (pendingSavedFeedRequest) {
      console.log(`[FeedExplorer] Cancelling previous pending saved feed request`)
      pendingSavedFeedRequest.abort()
    }
    
    await handleLoadCachedFeed()
  }
})

// Watch accountId changes and reload data
// Only trigger on user-initiated changes, not on initial mount
watch(accountId, async (newAccountId, oldAccountId) => {
  // CRITICAL: Only trigger if component is already mounted AND accountId actually changed
  // This prevents auto-loading stats when component first mounts
  if (!isMounted.value) {
    console.log(`[FeedExplorer] watch(accountId): Skipping - component not mounted yet`)
    return
  }
  
  if (!newAccountId || newAccountId === oldAccountId) {
    console.log(`[FeedExplorer] watch(accountId): Skipping - no accountId or same accountId`)
    return
  }
  
  console.log(`[FeedExplorer] Account changed: ${oldAccountId} -> ${newAccountId}`)
  // Sync to composable
  accountIdFromComposable.value = newAccountId
  profilePath.value = currentProfilePath.value
  // Clear current data
  feedItems.value = []
  userPosts.value = []
  selectedUser.value = null
  
  // Reset pagination when account changes
  currentPage.value = 1
  
  // CRITICAL: Check SYNCHRONOUSLY (no nextTick) to prevent race conditions
  const currentTab = activeTab.value
  
  // NEVER auto-load stats - stats should ONLY be loaded when user explicitly clicks "Refresh Status" button
  // This prevents browser from opening automatically
  sessionStatus.value = 'unknown'
  
  // Auto-load cached feed if on feed tab
  if (currentTab === 'feed') {
    await handleLoadCachedFeed(1)
  }
})

// Watch profilePathOverride to sync to composable
watch(profilePathOverride, (newPath) => {
  profilePath.value = newPath || currentProfilePath.value
})

onMounted(async () => {
  // Load accounts from store
  try {
    await fetchAccounts()
    // Set default account if available
    if (accountsStore.accounts.length > 0 && !accountId.value) {
      accountId.value = accountsStore.accounts[0].account_id
      accountIdFromComposable.value = accountId.value
    }
  } catch (err) {
    console.error('Failed to load accounts:', err)
    // Set error message for user feedback
    error.value = `Failed to load accounts: ${err.message || 'Unknown error'}. Please check your connection and try again.`
  }
  
  // Mark as mounted after a small delay to prevent watch from triggering on initial mount
  setTimeout(() => {
    isMounted.value = true
    
    // Auto-load cached feed when account is available AND on feed tab
    // DO NOT auto-load stats on mount - stats should only be loaded when:
    // 1. User explicitly clicks "Refresh Status" button
    // This prevents browser from opening unnecessarily
    if (accountId.value && activeTab.value === 'feed') {
      console.log(`[FeedExplorer] onMounted: Auto-loading cached feed from database`)
      console.log(`[FeedExplorer] onMounted: accountId=${accountId.value}, activeTab=${activeTab.value}, isMounted=${isMounted.value}`)
      handleLoadCachedFeed().catch(err => {
        console.error('[FeedExplorer] onMounted: Failed to load cached feed:', err)
        toast.error('Failed to load cached feed', err.message || 'Unknown error occurred')
      })
    } else {
      console.log(`[FeedExplorer] onMounted: Skipping cached feed load`, {
        accountId: accountId.value,
        activeTab: activeTab.value,
        isMounted: isMounted.value
      })
    }
  }, 100)
})
</script>

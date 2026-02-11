import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '@/components/layout/AppLayout.vue'
import Dashboard from '@/views/Dashboard.vue'
import Jobs from '@/views/Jobs.vue'
import ExcelUpload from '@/views/ExcelUpload.vue'
import Scheduler from '@/views/Scheduler.vue'
import Accounts from '@/views/Accounts.vue'
import Config from '@/views/Config.vue'
import Selectors from '@/views/Selectors.vue'
import FeedExplorer from '@/views/FeedExplorer.vue'

const routes = [
  {
    path: '/',
    component: AppLayout,
    children: [
      {
        path: '',
        name: 'dashboard',
        component: Dashboard,
        meta: { title: 'Dashboard' }
      },
      {
        path: 'jobs',
        name: 'jobs',
        component: Jobs,
        meta: { title: 'Jobs' }
      },
      {
        path: 'excel',
        name: 'excel',
        component: ExcelUpload,
        meta: { title: 'Excel Upload' }
      },
      {
        path: 'scheduler',
        name: 'scheduler',
        component: Scheduler,
        meta: { title: 'Scheduler' }
      },
      {
        path: 'accounts',
        name: 'accounts',
        component: Accounts,
        meta: { title: 'Accounts' }
      },
      {
        path: 'config',
        name: 'config',
        component: Config,
        meta: { title: 'Configuration' }
      },
      {
        path: 'selectors',
        name: 'selectors',
        component: Selectors,
        meta: { title: 'Selectors' }
      },
      {
        path: 'feed-explorer',
        name: 'feed-explorer',
        component: FeedExplorer,
        meta: { title: 'Feed Explorer' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

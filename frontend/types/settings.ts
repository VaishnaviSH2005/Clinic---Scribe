export interface NotificationPreferences {
  ai_processing_complete: boolean;
  report_generated: boolean;
  consultation_pending: boolean;
}

export interface ApplicationPreferences {
  default_dashboard_view: string;
  items_per_page: number;
}

export interface UserSettings {
  notification_preferences: NotificationPreferences;
  application_preferences: ApplicationPreferences;
}

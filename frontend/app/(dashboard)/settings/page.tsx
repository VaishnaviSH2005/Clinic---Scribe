"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ChangePasswordForm } from "@/features/authentication/components/change-password-form";
import { ProfileForm } from "@/features/authentication/components/profile-form";
import { useAuth } from "@/features/authentication/hooks/use-auth";
import { useProfile } from "@/features/authentication/hooks/use-profile";
import { DepartmentsTab } from "@/features/settings/components/departments-tab";
import { HospitalsTab } from "@/features/settings/components/hospitals-tab";
import { PreferencesTab } from "@/features/settings/components/preferences-tab";
import { UsersTab } from "@/features/settings/components/users-tab";

function ProfileTab() {
  const { data: profile, isLoading, isError } = useProfile();
  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Personal information</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading && (
            <div className="max-w-form space-y-4">
              <Skeleton className="h-11 w-full" />
              <Skeleton className="h-11 w-full" />
            </div>
          )}
          {isError && (
            <p className="text-body text-danger">Unable to load your profile. Please try again.</p>
          )}
          {profile && <ProfileForm profile={profile} />}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Change password</CardTitle>
        </CardHeader>
        <CardContent>
          <ChangePasswordForm />
        </CardContent>
      </Card>
    </div>
  );
}

export default function SettingsPage() {
  const { user } = useAuth();
  if (!user) return null;

  const canManageOrganization = user.role === "hospital_admin";
  const canManageHospital = user.role === "super_admin" || user.role === "hospital_admin";

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-h2 text-text-primary">Settings</h1>
        <p className="mt-1 text-body text-text-secondary">Manage your account and organization.</p>
      </div>

      <Tabs defaultValue="profile">
        <TabsList>
          <TabsTrigger value="profile">Profile</TabsTrigger>
          <TabsTrigger value="preferences">Preferences</TabsTrigger>
          {canManageHospital && <TabsTrigger value="hospital">Hospital</TabsTrigger>}
          {canManageOrganization && <TabsTrigger value="departments">Departments</TabsTrigger>}
          {canManageOrganization && <TabsTrigger value="users">Users</TabsTrigger>}
        </TabsList>

        <TabsContent value="profile">
          <ProfileTab />
        </TabsContent>
        <TabsContent value="preferences">
          <PreferencesTab />
        </TabsContent>
        {canManageHospital && (
          <TabsContent value="hospital">
            <HospitalsTab />
          </TabsContent>
        )}
        {canManageOrganization && (
          <TabsContent value="departments">
            <DepartmentsTab />
          </TabsContent>
        )}
        {canManageOrganization && (
          <TabsContent value="users">
            <UsersTab />
          </TabsContent>
        )}
      </Tabs>
    </div>
  );
}

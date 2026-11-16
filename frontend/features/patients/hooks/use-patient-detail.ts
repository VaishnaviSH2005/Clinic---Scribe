"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import type { MedicalProfile, PatientUpdatePayload } from "@/types/patient";

import { useHospitalScope } from "../hospital-scope";
import { patientService } from "../services/patient.service";

export function usePatient(id: string) {
  const hospitalId = useHospitalScope();
  return useQuery({
    queryKey: ["patients", id, hospitalId ?? null],
    queryFn: () => patientService.get(id, hospitalId),
    enabled: !!id,
  });
}

export function usePatientMedicalProfile(id: string) {
  const hospitalId = useHospitalScope();
  return useQuery({
    queryKey: ["patients", id, "medical-profile", hospitalId ?? null],
    queryFn: () => patientService.getMedicalProfile(id, hospitalId),
    enabled: !!id,
  });
}

export function usePatientTimeline(id: string) {
  const hospitalId = useHospitalScope();
  return useQuery({
    queryKey: ["patients", id, "timeline", hospitalId ?? null],
    queryFn: () => patientService.getTimeline(id, hospitalId),
    enabled: !!id,
  });
}

export function usePatientAppointments(id: string) {
  const hospitalId = useHospitalScope();
  return useQuery({
    queryKey: ["patients", id, "appointments", hospitalId ?? null],
    queryFn: () => patientService.getAppointments(id, hospitalId),
    enabled: !!id,
  });
}

export function usePatientDocuments(id: string) {
  const hospitalId = useHospitalScope();
  return useQuery({
    queryKey: ["patients", id, "documents", hospitalId ?? null],
    queryFn: () => patientService.getDocuments(id, hospitalId),
    enabled: !!id,
  });
}

export function usePatientDetailMutations(patientId: string) {
  const queryClient = useQueryClient();

  const updatePatient = useMutation({
    mutationFn: (payload: PatientUpdatePayload) => patientService.update(patientId, payload),
    onSuccess: () => {
      toast.success("Patient updated successfully.");
      void queryClient.invalidateQueries({ queryKey: ["patients", patientId] });
      void queryClient.invalidateQueries({ queryKey: ["patients"] });
    },
    onError: () => toast.error("Unable to update patient. Please try again."),
  });

  const updateMedicalProfile = useMutation({
    mutationFn: (payload: Partial<MedicalProfile>) =>
      patientService.updateMedicalProfile(patientId, payload),
    onSuccess: () => {
      toast.success("Medical information updated successfully.");
      void queryClient.invalidateQueries({ queryKey: ["patients", patientId, "medical-profile"] });
    },
    onError: () => toast.error("Unable to update medical information."),
  });

  const uploadDocument = useMutation({
    mutationFn: ({ file, category }: { file: File; category?: string }) =>
      patientService.uploadDocument(patientId, file, category),
    onSuccess: () => {
      toast.success("Document uploaded successfully.");
      void queryClient.invalidateQueries({ queryKey: ["patients", patientId, "documents"] });
      void queryClient.invalidateQueries({ queryKey: ["patients", patientId, "timeline"] });
    },
    onError: () => toast.error("Unable to upload the document. Please try again."),
  });

  return { updatePatient, updateMedicalProfile, uploadDocument };
}
